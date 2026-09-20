package config

import "testing"

func TestDefaultTargetsReturnsFreshSlice(t *testing.T) {
	first := DefaultTargets()
	first[0].Name = "changed-by-caller"

	second := DefaultTargets()
	if second[0].Name != "billing" {
		t.Fatalf("second default name = %q, want billing", second[0].Name)
	}
}

func TestLoadTargets(t *testing.T) {
	cases := []struct {
		name    string
		values  map[string]string
		want    Target
		wantErr bool
	}{
		{
			name:   "uses default when target is absent",
			values: map[string]string{},
			want:   Target{Name: "billing", Host: "billing.internal", Port: 8443},
		},
		{
			name:   "overrides endpoint from environment",
			values: map[string]string{"OPS_PROBE_TARGET": "payments.internal:9443"},
			want:   Target{Name: "billing", Host: "payments.internal", Port: 9443},
		},
		{
			name:    "requires host and port",
			values:  map[string]string{"OPS_PROBE_TARGET": "payments.internal"},
			wantErr: true,
		},
		{
			name:    "rejects port outside TCP range",
			values:  map[string]string{"OPS_PROBE_TARGET": "payments.internal:0"},
			wantErr: true,
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			targets, err := LoadTargets(func(key string) (string, bool) {
				value, found := tc.values[key]
				return value, found
			})
			if tc.wantErr {
				if err == nil {
					t.Fatal("LoadTargets() returned nil error")
				}
				return
			}
			if err != nil {
				t.Fatalf("LoadTargets() error = %v", err)
			}
			if len(targets) != 1 || targets[0] != tc.want {
				t.Fatalf("LoadTargets() = %+v, want [%+v]", targets, tc.want)
			}
		})
	}
}
