package main

import (
	"context"
	"example.com/golang-master/part6-testable-command/probe"
	"os"
)

func main() {
	runner := func(context.Context, probe.Endpoint) error { return nil }
	os.Exit(run(context.Background(), os.Stdout, os.Stderr, os.LookupEnv, runner))
}
