package main

import "testing"

func TestSeverity(t *testing.T) {
	cases := []struct {
		name   string
		status int
		want   string
	}{
		{name: "normal", status: 200, want: "normal"},
		{name: "warning", status: 404, want: "warning"},
		{name: "critical", status: 503, want: "critical"},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := severity(tc.status); got != tc.want {
				t.Fatalf("severity(%d) = %q, want %q", tc.status, got, tc.want)
			}
		})
	}
}
