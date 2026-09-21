package config

import "testing"

func TestLoadTargetsUsesDefaultOrOverride(t *testing.T) {
	tests := []struct {
		name  string
		raw   string
		found bool
		want  Target
	}{
		{
			name:  "uses the documented default when the variable is absent",
			want:  Target{Name: "billing", Host: "billing.internal", Port: 8443},
			found: false,
		},
		{
			name:  "maps a host and port from the override",
			raw:   "payments.internal:9443",
			found: true,
			want:  Target{Name: "billing", Host: "payments.internal", Port: 9443},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			targets, err := LoadTargets(func(key string) (string, bool) {
				if key != "OPS_PROBE_TARGET" {
					t.Fatalf("lookup key = %q", key)
				}
				return tt.raw, tt.found
			})
			if err != nil {
				t.Fatalf("LoadTargets() error = %v", err)
			}
			if len(targets) != 1 || targets[0] != tt.want {
				t.Fatalf("LoadTargets() = %+v, want %+v", targets, tt.want)
			}
		})
	}
}

func TestLoadTargetsRejectsMalformedOverrides(t *testing.T) {
	tests := []struct {
		name string
		raw  string
	}{
		{name: "missing port", raw: "payments.internal"},
		{name: "empty host", raw: ":8443"},
		{name: "non-numeric port", raw: "payments.internal:https"},
		{name: "port zero", raw: "payments.internal:0"},
		{name: "port above TCP range", raw: "payments.internal:65536"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := LoadTargets(func(string) (string, bool) {
				return tt.raw, true
			})
			if err == nil {
				t.Fatalf("LoadTargets(%q) returned nil error", tt.raw)
			}
		})
	}
}
