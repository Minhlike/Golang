package main

import (
	"context"
	"fmt"
	"os"

	"example.com/golang-master/part6-testable-command/internal/app"
	"example.com/golang-master/part6-testable-command/probe"
)

func main() {
	runner := func(context.Context, probe.Endpoint) error { return nil }
	outcomes, err := app.Run(context.Background(), os.LookupEnv, runner)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}

	for _, outcome := range outcomes {
		if outcome.Err != nil {
			fmt.Printf("%s: %v\n", outcome.Service, outcome.Err)
			continue
		}
		fmt.Printf("%s healthy=true\n", outcome.Service)
	}
}
