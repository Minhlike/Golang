package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestRejectsUnsafeOptions(t *testing.T) {
	valid := options{mode: "slice", cycles: 1, items: 1, bytes: 16, limit: 1}
	for _, mutate := range []func(*options){
		func(o *options) { o.mode = "unknown" },
		func(o *options) { o.cycles = 0 },
		func(o *options) { o.bytes = 15 },
		func(o *options) { o.cycles, o.items, o.bytes = 20, 256, 64<<20 },
		func(o *options) { o.mode, o.cycles, o.items = "goroutine", 20, 256 },
	} {
		o := valid
		mutate(&o)
		if err := run(o); err == nil {
			t.Fatal("unsafe options accepted")
		}
	}
}

func TestAllFixturesWriteProfilesAndCleanUp(t *testing.T) {
	for _, mode := range []string{"slice", "cache", "churn", "goroutine", "ticker", "context"} {
		for _, repaired := range []bool{false, true} {
			dir := t.TempDir()
			if err := run(options{mode: mode, out: dir, fixed: repaired,
				cycles: 1, items: 1, bytes: 16, limit: 1}); err != nil {
				t.Fatal(err)
			}
			for _, name := range []string{"00.heap.pprof", "01.heap.pprof",
				"02.heap.pprof", "02.goroutines.txt"} {
				info, err := os.Stat(filepath.Join(dir, name))
				if err != nil || info.Size() == 0 {
					t.Fatalf("missing/nonempty profile %s: %v", name, err)
				}
			}
		}
	}
}
