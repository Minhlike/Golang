// Package failurelab adds a bounded streaming admission experiment around
// the existing probe and telemetry packages. It is not a new opsprobe API.
package failurelab

import (
	"context"
	"errors"
	"sync"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/probe"
	"example.com/golang-master/projects/opsprobe/internal/telemetry"
	"github.com/prometheus/client_golang/prometheus"
)

var ErrFull = errors.New("admission queue full")
var ErrClosed = errors.New("admission closed")

type job struct {
	target   probe.Target
	admitted time.Time
}
type Stats struct {
	Accepted, Rejected, Completed, Dropped int
	Running, PeakRunning, Queue, PeakQueue int
}
type Runner struct {
	ctx     context.Context
	cancel  context.CancelFunc
	mu      sync.Mutex
	closed  bool
	jobs    chan job
	results chan probe.Result
	done    chan struct{}
	stats   Stats
	queue   prometheus.GaugeFunc
	running prometheus.Gauge
	shed    prometheus.Counter
	latency prometheus.Histogram
}

func offer(ctx context.Context, out chan<- probe.Result, r probe.Result) {
	select {
	case out <- r:
	case <-ctx.Done():
	}
}

// Queue delay is INCLUDED in each admitted job's deadline budget. No retries.
// Caller must Cancel and join Done if it stops consuming Results.
func New(ctx context.Context, workers, capacity int, budget time.Duration,
	p *probe.Pool, tel *telemetry.Telemetry) (*Runner, error) {
	return newRunner(ctx, workers, capacity, budget, p, tel, offer)
}

func newRunner(ctx context.Context, workers, capacity int, budget time.Duration,
	p *probe.Pool, tel *telemetry.Telemetry,
	send func(context.Context, chan<- probe.Result, probe.Result)) (*Runner, error) {
	if workers < 1 || workers > 32 || capacity < 1 || capacity > 1024 || budget <= 0 || p == nil || tel == nil {
		return nil, errors.New("invalid bounded runner configuration")
	}
	ctx, cancel := context.WithCancel(ctx)
	r := &Runner{ctx: ctx, cancel: cancel, jobs: make(chan job, capacity),
		results: make(chan probe.Result), done: make(chan struct{})}
	r.queue = prometheus.NewGaugeFunc(prometheus.GaugeOpts{
		Name: "failurelab_queue_depth", Help: "Jobs awaiting a worker, not results awaiting consumer."}, func() float64 { return float64(len(r.jobs)) })
	r.running = prometheus.NewGauge(prometheus.GaugeOpts{Name: "failurelab_running", Help: "Probes currently executing."})
	r.shed = prometheus.NewCounter(prometheus.CounterOpts{Name: "failurelab_rejected_total", Help: "Admission rejected because queue full."})
	r.latency = prometheus.NewHistogram(prometheus.HistogramOpts{Name: "failurelab_job_seconds", Help: "Admission to probe completion, excludes result delivery."})
	// A private registry per experiment; no global collectors or remote export.
	registered := []prometheus.Collector{}
	for _, c := range []prometheus.Collector{r.queue, r.running, r.shed, r.latency} {
		if err := tel.Registry.Register(c); err != nil {
			cancel()
			for _, prior := range registered {
				tel.Registry.Unregister(prior)
			}
			return nil, err
		}
		registered = append(registered, c)
	}
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				if ctx.Err() != nil {
					return
				}
				select {
				case <-ctx.Done():
					return
				case j, ok := <-r.jobs:
					if !ok || ctx.Err() != nil {
						return
					}
					deadline := j.admitted.Add(budget)
					jobCtx, stop := context.WithDeadline(ctx, deadline)
					r.mu.Lock()
					r.stats.Running++
					if r.stats.Running > r.stats.PeakRunning {
						r.stats.PeakRunning = r.stats.Running
					}
					r.mu.Unlock()
					r.running.Inc()
					result := p.ProbeSingle(jobCtx, j.target)
					stop()
					r.running.Dec()
					tel.RecordProbe(result.TargetID, result.URL, string(result.Outcome), float64(result.DurationNs)/1e9, result.Error)
					r.latency.Observe(time.Since(j.admitted).Seconds())
					r.mu.Lock()
					r.stats.Running--
					r.stats.Completed++
					r.mu.Unlock()
					send(ctx, r.results, result)
				}
			}
		}()
	}
	go func() {
		wg.Wait()
		r.CloseAdmission()
		// Cancellation may leave accepted jobs unstarted. Release their payloads
		// before acknowledging completion, even while the registry owns r.queue.
		for range r.jobs {
			r.mu.Lock()
			r.stats.Dropped++
			r.mu.Unlock()
		}
		r.cancel()
		close(r.results)
		close(r.done)
	}()
	return r, nil
}

// Submit sheds immediately when capacity is exhausted. It creates no goroutine.
func (r *Runner) Submit(target probe.Target) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.closed || r.ctx.Err() != nil {
		return ErrClosed
	}
	select {
	case r.jobs <- job{target: target, admitted: time.Now()}:
		r.stats.Accepted++
		if n := len(r.jobs); n > r.stats.PeakQueue {
			r.stats.PeakQueue = n
		}
		return nil
	default:
		r.stats.Rejected++
		r.shed.Inc()
		return ErrFull
	}
}

func (r *Runner) CloseAdmission() {
	r.mu.Lock()
	defer r.mu.Unlock()
	if !r.closed {
		r.closed = true
		close(r.jobs)
	}
}
func (r *Runner) Cancel()                      { r.cancel(); r.CloseAdmission() }
func (r *Runner) Results() <-chan probe.Result { return r.results }
func (r *Runner) Done() <-chan struct{}        { return r.done }
func (r *Runner) Stats() Stats {
	r.mu.Lock()
	defer r.mu.Unlock()
	v := r.stats
	v.Queue = len(r.jobs)
	return v
}
