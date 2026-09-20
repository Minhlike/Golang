package portcheck

import "testing"

func TestParsePort(t *testing.T) {
	tests := []struct {
		name    string
		raw     string
		want    int
		wantErr bool
	}{
		{name: "lowest valid port", raw: "1", want: 1},
		{name: "common HTTPS port", raw: "443", want: 443},
		{name: "highest valid port", raw: "65535", want: 65535},
		{name: "zero is outside range", raw: "0", wantErr: true},
		{name: "too large", raw: "65536", wantErr: true},
		{name: "not a number", raw: "eighty", wantErr: true},
	}

	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			got, err := ParsePort(test.raw)
			if test.wantErr {
				if err == nil {
					t.Fatal("ParsePort returned nil error")
				}
				return
			}
			if err != nil {
				t.Fatalf("ParsePort returned error: %v", err)
			}
			if got != test.want {
				t.Fatalf("ParsePort(%q) = %d, want %d", test.raw, got, test.want)
			}
		})
	}
}
