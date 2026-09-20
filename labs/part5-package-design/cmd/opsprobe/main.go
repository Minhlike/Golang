package main

import (
	"context"
	"fmt"

	"example.com/golang-master/part5-package-design/internal/config"
	"example.com/golang-master/part5-package-design/probe"
)

func main() {
	ctx := context.Background()
	run := func(context.Context, probe.Endpoint) error {
		return nil
	}

	for _, target := range config.DefaultTargets() {
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
		fmt.Printf("%s healthy=%t\n", result.Service, result.Healthy)
	}
}
