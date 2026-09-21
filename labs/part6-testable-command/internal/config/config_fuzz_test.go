package config

import "testing"

func lookup(raw string) LookupEnv {
	return func(string) (string, bool) {
		return raw, raw != ""
	}
}

func FuzzLoadTargetsNeverReturnsInvalidTarget(f *testing.F) {
	for _, seed := range []string{
		"",
		"billing.internal:8443",
		"[2001:db8::10]:443",
		"payments.internal:0",
		"not a target",
	} {
		f.Add(seed)
	}

	f.Fuzz(func(t *testing.T, raw string) {
		targets, err := LoadTargets(lookup(raw))
		if err != nil {
			return
		}
		if len(targets) != 1 {
			t.Fatalf("LoadTargets(%q) returned %d targets", raw, len(targets))
		}
		target := targets[0]
		if target.Host == "" || target.Port < 1 || target.Port > 65535 {
			t.Fatalf("LoadTargets(%q) returned invalid target %+v", raw, target)
		}
	})
}
