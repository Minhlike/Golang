package main

import (
	"context"
	"fmt"
	"os"

	"example.com/golang-master/part5-package-design/internal/config"
	"example.com/golang-master/part5-package-design/probe"
)

func main() {
	ctx := context.Background()
	run := func(context.Context, probe.Endpoint) error {
		return nil
	}

	targets, err := config.LoadTargets(os.LookupEnv)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}

	for _, target := range targets {
		service := probe.Service{
			Name: target.Name,
			Endpoint: probe.Endpoint{
				Host: target.Host,
				Port: target.Port,
			},
		}
		result, err := probe.Check(ctx, service, run)
		if err != nil {
			fmt.Printf("%s: %v\n", service.Name, err)
			continue
		}
		fmt.Printf("%s healthy=true\n", result.Service)
	}
}
