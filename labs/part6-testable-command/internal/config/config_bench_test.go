package config

import "testing"

func BenchmarkLoadTargets(b *testing.B) {
	tests := []struct {
		name string
		raw  string
	}{
		{name: "default", raw: ""},
		{name: "hostname override", raw: "payments.internal:9443"},
		{name: "IPv6 override", raw: "[2001:db8::10]:443"},
	}

	for _, tt := range tests {
		b.Run(tt.name, func(b *testing.B) {
			lookup := func(string) (string, bool) {
				return tt.raw, tt.raw != ""
			}
			b.ReportAllocs()
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				if _, err := LoadTargets(lookup); err != nil {
					b.Fatal(err)
				}
			}
		})
	}
}
