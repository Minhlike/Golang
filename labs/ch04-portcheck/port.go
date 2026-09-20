// Package portcheck parses one TCP port from a human-provided configuration value.
package portcheck

import (
	"fmt"
	"strconv"
)

// ParsePort returns a valid TCP port in the inclusive range 1..65535.
func ParsePort(raw string) (int, error) {
	port, err := strconv.Atoi(raw)
	if err != nil {
		return 0, fmt.Errorf("parse port %q: %w", raw, err)
	}
	if port < 1 || port > 65535 {
		return 0, fmt.Errorf("port %d is outside 1..65535", port)
	}
	return port, nil
}
