// Package config provides application-private target defaults.
package config

import (
	"fmt"
	"net"
	"strconv"
)

// Target is configuration-shaped data before it is mapped to a probe service.
type Target struct {
	Name string
	Host string
	Port int
}

// LookupEnv reads one environment value without coupling configuration to os.
type LookupEnv func(string) (string, bool)

// DefaultTargets returns fresh target data owned by its caller.
func DefaultTargets() []Target {
	return []Target{
		{Name: "billing", Host: "billing.internal", Port: 8443},
	}
}

// LoadTargets applies an optional OPS_PROBE_TARGET host:port override.
func LoadTargets(lookup LookupEnv) ([]Target, error) {
	targets := DefaultTargets()
	raw, found := lookup("OPS_PROBE_TARGET")
	if !found || raw == "" {
		return targets, nil
	}

	host, portText, err := net.SplitHostPort(raw)
	if err != nil {
		return nil, fmt.Errorf("parse OPS_PROBE_TARGET %q: %w", raw, err)
	}
	if host == "" {
		return nil, fmt.Errorf("parse OPS_PROBE_TARGET %q: host is empty", raw)
	}
	port, err := strconv.Atoi(portText)
	if err != nil {
		return nil, fmt.Errorf("parse OPS_PROBE_TARGET port %q: %w", portText, err)
	}
	if port < 1 || port > 65535 {
		return nil, fmt.Errorf("parse OPS_PROBE_TARGET: port %d is outside 1..65535", port)
	}

	targets[0].Host = host
	targets[0].Port = port
	return targets, nil
}
