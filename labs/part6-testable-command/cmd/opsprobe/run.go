package main

import (
	"context"
	"fmt"
	"io"

	"example.com/golang-master/part6-testable-command/internal/app"
	"example.com/golang-master/part6-testable-command/internal/config"
	"example.com/golang-master/part6-testable-command/probe"
)

func run(ctx context.Context, out, errOut io.Writer, lookup config.LookupEnv, runner probe.Runner) int {
	outcomes, err := app.Run(ctx, lookup, runner)
	if err != nil {
		fmt.Fprintln(errOut, err)
		return 2
	}
	for _, outcome := range outcomes {
		if outcome.Err != nil {
			fmt.Fprintf(out, "%s: %v\n", outcome.Service, outcome.Err)
			continue
		}
		fmt.Fprintf(out, "%s healthy=true\n", outcome.Service)
	}
	return 0
}
