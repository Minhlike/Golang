// investigate runs bounded local workloads. Profiles are files, never HTTP endpoints.
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"runtime/pprof"
	"time"

	"example.com/golang-master/part10-resource-retention/baseline"
	"example.com/golang-master/part10-resource-retention/fixed"
)

type options struct {
	mode, out     string
	fixed         bool
	cycles, items int
	bytes, limit  int
}

type cacheStore interface {
	Put(string, []byte) error
	Len() int
}

func main() {
	var o options
	flag.StringVar(&o.mode, "mode", "slice", "slice/cache/churn/goroutine/ticker/context")
	flag.StringVar(&o.out, "out", "artifacts/run", "local profile directory; empty disables files")
	flag.BoolVar(&o.fixed, "fixed", false, "use repaired ownership")
	flag.IntVar(&o.cycles, "cycles", 4, "workload cycles, 1..20")
	flag.IntVar(&o.items, "items", 2, "items per cycle, 1..256")
	flag.IntVar(&o.bytes, "bytes", 1<<20, "payload bytes, 16..64 MiB")
	flag.IntVar(&o.limit, "limit", 4, "cache entry limit, 1..256")
	flag.Parse()
	if err := run(o); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(o options) error {
	if o.cycles < 1 || o.cycles > 20 || o.items < 1 || o.items > 256 ||
		o.bytes < 16 || o.bytes > 64<<20 || o.limit < 1 || o.limit > 256 {
		return fmt.Errorf("options exceed lab bounds")
	}
	switch o.mode {
	case "slice", "cache", "churn":
		if o.cycles*o.items > (256<<20)/o.bytes {
			return fmt.Errorf("requested payload exceeds 256 MiB lab budget")
		}
	case "goroutine", "ticker":
		if o.cycles*o.items > 128 {
			return fmt.Errorf("requested workers exceed 128-worker lab budget")
		}
	case "context":
	default:
		return fmt.Errorf("unknown mode %q", o.mode)
	}
	if o.out != "" {
		if err := os.MkdirAll(o.out, 0755); err != nil {
			return err
		}
	}
	// Full allocation sampling is deliberately expensive: a small lab only.
	runtime.MemProfileRate = 1
	fmt.Printf("go=%s target=%s/%s mode=%s fixed=%t\n",
		runtime.Version(), runtime.GOOS, runtime.GOARCH, o.mode, o.fixed)
	fmt.Printf("cycles=%d items=%d bytes=%d limit=%d MemProfileRate=1\n",
		o.cycles, o.items, o.bytes, o.limit)
	fmt.Println("cycle,entries,goroutines,HeapAlloc,HeapInuse,HeapSys,HeapReleased,TotalAlloc")
	parent, cancelParent := context.WithCancel(context.Background())
	defer cancelParent()
	var views [][]byte
	var cache cacheStore
	if o.mode == "cache" {
		if o.fixed {
			var err error
			cache, err = fixed.NewCache(o.limit, o.bytes)
			if err != nil {
				return err
			}
		} else {
			cache = baseline.NewCache()
		}
	}
	var done []<-chan struct{}
	var rescues []chan struct{}
	cleanup := func() {
		cancelParent()
		for _, rescue := range rescues {
			close(rescue)
		}
		for _, exit := range done {
			<-exit
		}
		rescues, done = nil, nil
	}
	defer func() { cleanup() }()
	if err := observe(o.out, 0, 0); err != nil {
		return err
	}
	for cycle := 1; cycle <= o.cycles; cycle++ {
		for item := 0; item < o.items; item++ {
			switch o.mode {
			case "slice":
				buf := payload(o.bytes)
				if o.fixed {
					views = append(views, fixed.Prefix(buf, 16))
				} else {
					views = append(views, baseline.Prefix(buf, 16))
				}
			case "cache":
				key := fmt.Sprintf("%d/%d", cycle, item)
				if err := cache.Put(key, payload(o.bytes)); err != nil {
					return err
				}
			case "churn":
				runtime.KeepAlive(payload(o.bytes))
			case "goroutine", "ticker":
				ctx, cancel := context.WithCancel(parent)
				rescue := make(chan struct{})
				var exit <-chan struct{}
				if o.mode == "goroutine" {
					started := make(chan struct{})
					if o.fixed {
						exit = fixed.Wait(ctx, rescue, started)
					} else {
						exit = baseline.Wait(ctx, rescue, started)
					}
					<-started
				} else if o.fixed {
					w := fixed.RunTicker(ctx, time.Hour, rescue, func(context.Context) {})
					<-w.Started
					exit = w.Done
				} else {
					w := baseline.RunTicker(ctx, time.Hour, rescue, func(context.Context) {})
					<-w.Started
					exit = w.Done
				}
				cancel()
				if o.fixed {
					<-exit // Lifecycle evidence, not a goroutine-count threshold.
				}
				rescues, done = append(rescues, rescue), append(done, exit)
			case "context":
				work := func(context.Context) error { return nil }
				var err error
				if o.fixed {
					err = fixed.DoTimeout(parent, time.Hour, work)
				} else {
					err = baseline.DoTimeout(parent, time.Hour, work)
				}
				if err != nil {
					return err
				}
			}
		}
		entries := len(views)
		if cache != nil {
			entries = cache.Len()
		}
		if err := observe(o.out, cycle, entries); err != nil {
			return err
		}
		runtime.KeepAlive(views)
		runtime.KeepAlive(cache)
		runtime.KeepAlive(parent)
	}
	cleanup()
	views, cache = nil, nil
	return observe(o.out, o.cycles+1, 0)
}

//go:noinline
func payload(n int) []byte {
	buf := make([]byte, n)
	for i := range buf {
		buf[i] = byte(i)
	}
	return buf
}

func observe(out string, cycle, entries int) error {
	// Heap profiles can lag collection; complete two cycles for this experiment.
	runtime.GC()
	runtime.GC()
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	fmt.Printf("%d,%d,%d,%d,%d,%d,%d,%d\n", cycle, entries,
		runtime.NumGoroutine(), m.HeapAlloc, m.HeapInuse,
		m.HeapSys, m.HeapReleased, m.TotalAlloc)
	if out == "" {
		return nil
	}
	if err := writeProfile(filepath.Join(out, fmt.Sprintf("%02d.heap.pprof", cycle)), "heap", 0); err != nil {
		return err
	}
	return writeProfile(filepath.Join(out, fmt.Sprintf("%02d.goroutines.txt", cycle)), "goroutine", 2)
}

func writeProfile(path, name string, debug int) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	writeErr := pprof.Lookup(name).WriteTo(f, debug)
	closeErr := f.Close()
	if writeErr != nil {
		return writeErr
	}
	return closeErr
}
