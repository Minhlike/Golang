package contracts

import (
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func writeModuleFixture(t *testing.T, root, name, content string) {
	t.Helper()
	path := filepath.Join(root, name)
	if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), 0600); err != nil {
		t.Fatal(err)
	}
}

func TestInternalBoundaryUsesModuleImportPaths(t *testing.T) {
	root := t.TempDir()
	writeModuleFixture(t, root, "parent/go.mod", "module example.com/parent\ngo 1.27.0\n")
	writeModuleFixture(t, root, "parent/internal/private/p.go", "package private\nconst Value = 1\n")
	for _, tc := range []struct {
		name, module string
		allowed      bool
	}{
		{"inside", "example.com/parent/consumer", true},
		{"outside", "example.com/other", false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			dir := filepath.Join(root, "parent", tc.name)
			writeModuleFixture(t, dir, "go.mod", "module "+tc.module+"\ngo 1.27.0\nrequire example.com/parent v0.0.0\nreplace example.com/parent => ..\n")
			writeModuleFixture(t, dir, "consumer.go", "package consumer\nimport \"example.com/parent/internal/private\"\nvar Value = private.Value\n")
			cmd := exec.Command("go", "test", "./...")
			cmd.Dir = dir
			cmd.Env = append(os.Environ(), "GOWORK=off", "GOTOOLCHAIN=local", "GOPROXY=off", "GOSUMDB=off")
			output, err := cmd.CombinedOutput()
			if (err == nil) != tc.allowed || (!tc.allowed && !strings.Contains(string(output), "use of internal package")) {
				t.Fatalf("allowed=%v err=%v\n%s", tc.allowed, err, output)
			}
			t.Logf("path=%s allowed=%v output=%s", tc.module, tc.allowed, output)
		})
	}
}

func TestMVSSelectsHighestRequiredVersion(t *testing.T) {
	root := t.TempDir()
	proxy := filepath.Join(root, "proxy")
	for _, version := range []string{"v1.0.0", "v1.2.0", "v1.3.0"} {
		writeModuleFixture(t, proxy, "example.com/b/@v/"+version+".mod", "module example.com/b\ngo 1.27.0\n")
		writeModuleFixture(t, proxy, "example.com/b/@v/"+version+".info", `{"Version":"`+version+`","Time":"2026-01-01T00:00:00Z"}`)
	}
	writeModuleFixture(t, proxy, "example.com/b/@v/list", "v1.0.0\nv1.2.0\nv1.3.0\n")
	writeModuleFixture(t, proxy, "example.com/c/@v/v1.0.0.mod", "module example.com/c\ngo 1.27.0\nrequire example.com/b v1.2.0\n")
	writeModuleFixture(t, proxy, "example.com/c/@v/v1.0.0.info", `{"Version":"v1.0.0","Time":"2026-01-01T00:00:00Z"}`)
	main := filepath.Join(root, "main")
	writeModuleFixture(t, main, "go.mod", "module example.com/a\ngo 1.27.0\nrequire (\nexample.com/b v1.0.0\nexample.com/c v1.0.0\n)\n")
	proxyPath := filepath.ToSlash(proxy)
	if filepath.VolumeName(proxy) != "" {
		proxyPath = "/" + proxyPath
	}
	proxyURL := (&url.URL{Scheme: "file", Path: proxyPath}).String()
	cmd := exec.Command("go", "list", "-mod=mod", "-m", "all")
	cmd.Dir = main
	cmd.Env = append(os.Environ(), "GOWORK=off", "GOTOOLCHAIN=local", "GOPROXY="+proxyURL,
		"GONOPROXY=none", "GONOSUMDB=*", "GOSUMDB=off", "GOMODCACHE="+filepath.Join(root, "modcache"))
	output, err := cmd.CombinedOutput()
	if err != nil || !strings.Contains(string(output), "example.com/b v1.2.0") || strings.Contains(string(output), "example.com/b v1.3.0") {
		t.Fatalf("MVS selection: %v\n%s", err, output)
	}
	t.Logf("offline file proxy, selected build list:\n%s", output)
}
