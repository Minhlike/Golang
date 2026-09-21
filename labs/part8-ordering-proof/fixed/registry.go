// Package fixed is a reference for the ordering-proof lab.
package fixed

import "sync"

// Report is one worker's completed outcome.
type Report struct {
	Target string
}

// Registry owns reports shared by worker goroutines and their coordinator.
type Registry struct {
	mu      sync.Mutex
	reports []Report
}

// Add records one completed report.
func (r *Registry) Add(report Report) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.reports = append(r.reports, report)
}

// Snapshot returns a copy that callers may change independently.
func (r *Registry) Snapshot() []Report {
	r.mu.Lock()
	defer r.mu.Unlock()

	snapshot := make([]Report, len(r.reports))
	copy(snapshot, r.reports)
	return snapshot
}
