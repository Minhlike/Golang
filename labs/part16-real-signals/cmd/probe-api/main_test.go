package main

import "testing"

func TestListenAddress(t *testing.T) {
	for _, tc := range []struct {
		port string
		want string
		ok   bool
	}{
		{"", ":8080", true},
		{"18080", ":18080", true},
		{"0", "", false},
		{"not-a-port", "", false},
	} {
		got, err := listenAddress(tc.port)
		if (err == nil) != tc.ok || got != tc.want {
			t.Fatalf("listenAddress(%q) = %q, %v", tc.port, got, err)
		}
	}
}
