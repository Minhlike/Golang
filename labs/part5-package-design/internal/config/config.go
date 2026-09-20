// Package config provides application-private target defaults.
package config

// Target is configuration-shaped data before it is mapped to a probe service.
type Target struct {
	Name string
	Host string
	Port int
}

// DefaultTargets returns fresh target data owned by its caller.
func DefaultTargets() []Target {
	return []Target{
		{Name: "billing", Host: "billing.internal", Port: 8443},
	}
}
