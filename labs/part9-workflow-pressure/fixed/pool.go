package fixed

import (
	"context"
	"sync"
)

type Job struct {
	Name string
}

type Result struct {
	Job Job
	Err error
}

type Work func(context.Context, Job) error

func Run(ctx context.Context, jobs []Job, workers int, work Work) <-chan Result {
	out := make(chan Result)
	if workers <= 0 {
		close(out)
		return out
	}

	in := make(chan Job)
	var workersDone sync.WaitGroup
	workersDone.Add(workers)

	for range workers {
		go func() {
			defer workersDone.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case job, ok := <-in:
					if !ok {
						return
					}
					result := Result{Job: job, Err: work(ctx, job)}
					if ctx.Err() != nil {
						return
					}
					select {
					case out <- result:
					case <-ctx.Done():
						return
					}
				}
			}
		}()
	}

	go func() {
		defer close(in)
		for _, job := range jobs {
			select {
			case in <- job:
			case <-ctx.Done():
				return
			}
		}
	}()

	go func() {
		workersDone.Wait()
		close(out)
	}()

	return out
}
