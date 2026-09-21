package fixed

import (
	"fmt"
	"sync"
	"testing"
)

func TestRegistryKeepsCompletedReports(t *testing.T) {
	const workers = 64

	var registry Registry
	var wg sync.WaitGroup
	wg.Add(workers)
	for i := 0; i < workers; i++ {
		go func(id int) {
			defer wg.Done()
			registry.Add(Report{Target: fmt.Sprintf("target-%02d", id)})
		}(i)
	}
	wg.Wait()

	reports := registry.Snapshot()
	if len(reports) != workers {
		t.Fatalf("len(Snapshot()) = %d, want %d", len(reports), workers)
	}
	seen := make(map[string]bool, workers)
	for _, report := range reports {
		seen[report.Target] = true
	}
	for i := 0; i < workers; i++ {
		want := fmt.Sprintf("target-%02d", i)
		if !seen[want] {
			t.Fatalf("Snapshot() missing %q", want)
		}
	}
}

func TestSnapshotDoesNotShareRegistrySlice(t *testing.T) {
	var registry Registry
	registry.Add(Report{Target: "billing"})

	snapshot := registry.Snapshot()
	snapshot[0] = Report{Target: "mutated-by-caller"}

	if got := registry.Snapshot()[0].Target; got != "billing" {
		t.Fatalf("registry was mutated through Snapshot(): %q", got)
	}
}
