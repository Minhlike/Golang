package contracts

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestAtlasCompilerDiagnosticAndTerminatingStatements(t *testing.T) {
	for _, tc := range []struct {
		name, source, diagnostic string
		accept                   bool
	}{
		{"A04", "package p\nfunc f(){x:=1}\n", "declared and not used: x", false},
		{"A02 blank only", "package p\nfunc f(){_ := 1}\n", "no new variables", false},
		{"A07", "package p\nfunc f() int {}\n", "missing return", false},
		{"A07 infinite loop", "package p\nfunc f() int {for{}}\n", "", true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			dir := t.TempDir()
			file := filepath.Join(dir, "case.go")
			if err := os.WriteFile(file, []byte(tc.source), 0600); err != nil {
				t.Fatal(err)
			}
			cmd := exec.Command("go", "build", file)
			cmd.Dir = dir
			cmd.Env = append(os.Environ(), "GOWORK=off", "GOTOOLCHAIN=local")
			out, err := cmd.CombinedOutput()
			if (err == nil) != tc.accept || (!tc.accept && !strings.Contains(string(out), tc.diagnostic)) {
				t.Fatalf("accept=%v err=%v output=%s", tc.accept, err, out)
			}
			t.Logf("compiler diagnostic: %s", out)
		})
	}
}
