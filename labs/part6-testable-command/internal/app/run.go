// Package app coordinates configured probes without owning process I/O.
package app

import (
	"context"
	"errors"

	"example.com/golang-master/part6-testable-command/internal/config"
	"example.com/golang-master/part6-testable-command/probe"
)

// Outcome records the result of attempting one configured service.
type Outcome struct {
	Service string
	Err     error
}

// Run loads targets and probes each one without reading process I/O or printing.
func Run(ctx context.Context, lookup config.LookupEnv, runner probe.Runner) ([]Outcome, error) {
	targets, err := config.LoadTargets(lookup)
	if err != nil {
		return nil, err
	}

	outcomes := make([]Outcome, 0, len(targets))
	for _, target := range targets {
		service := probe.Service{
			Name: target.Name,
			Endpoint: probe.Endpoint{
				Host: target.Host,
				Port: target.Port,
			},
		}
		result, err := probe.Check(ctx, service, runner)
		if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
			return nil, err
		}
		if err != nil {
			outcomes = append(outcomes, Outcome{Service: service.Name, Err: err})
			continue
		}
		outcomes = append(outcomes, Outcome{Service: result.Service})
	}
	return outcomes, nil
}
