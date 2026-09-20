package main

import (
	"context"
	"fmt"
)

type endpoint struct {
	host string
	port int
}

type target struct {
	name string
	host string
	port int
}

func defaultTargets() []target {
	return []target{{name: "billing", host: "billing.internal", port: 8443}}
}

func check(ctx context.Context, name string, endpoint endpoint, run func(context.Context, endpoint) error) (bool, error) {
	if err := ctx.Err(); err != nil {
		return false, fmt.Errorf("check %q: %w", name, err)
	}
	if err := run(ctx, endpoint); err != nil {
		return false, fmt.Errorf("check %q: %w", name, err)
	}
	return true, nil
}

func main() {
	run := func(context.Context, endpoint) error { return nil }
	for _, target := range defaultTargets() {
		healthy, err := check(context.Background(), target.name, endpoint{host: target.host, port: target.port}, run)
		if err != nil {
			fmt.Printf("%s: %v\n", target.name, err)
			continue
		}
		fmt.Printf("%s healthy=%t\n", target.name, healthy)
	}
}
