package contracts

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

// Each compiler case establishes only acceptance/rejection of this tiny source.
// It does not prove package initialization order or deployment properties.
func TestImportUsageBoundaries(t *testing.T) {
	cases := []struct {
		name   string
		imp    string
		body   string
		accept bool
	}{
		{"ordinary-unused", `import "fmt"`, "", false},
		{"dot-unused", `import . "fmt"`, "", false},
		{"dot-used", `import . "fmt"`, `Println("ok")`, true},
		{"blank", `import _ "fmt"`, "", true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			dir := t.TempDir()
			source := "package main\n" + tc.imp + "\nfunc main(){" + tc.body + "}\n"
			path := filepath.Join(dir, "main.go")
			if err := os.WriteFile(path, []byte(source), 0600); err != nil {
				t.Fatal(err)
			}
			cmd := exec.Command("go", "build", "-o", filepath.Join(dir, "program.exe"), path)
			cmd.Env = append(os.Environ(), "GOWORK=off", "GOTOOLCHAIN=local")
			output, err := cmd.CombinedOutput()
			if (err == nil) != tc.accept {
				t.Fatalf("accept=%v: %v\n%s", tc.accept, err, output)
			}
			if !tc.accept && !strings.Contains(string(output), "imported and not used") {
				t.Fatalf("wrong rejection: %s", output)
			}
		})
	}
}

func TestShortDeclarationScopeTrace(t *testing.T) {
	x := 1
	x, y := 2, 3
	{
		x := 4
		if x != 4 || y != 3 {
			t.Fatal("inner binding")
		}
	}
	if x != 2 || y != 3 {
		t.Fatal("same-block redeclaration must reuse x")
	}
}

func TestIotaCountsSpecsNotPhysicalLines(t *testing.T) {
	const (
		a, b = iota, iota
		c    = iota
	)
	if a != 0 || b != 0 || c != 1 {
		t.Fatal("iota advances once per ConstSpec")
	}
}
