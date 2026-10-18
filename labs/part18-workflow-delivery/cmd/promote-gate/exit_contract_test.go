package main

import (
	"context"
	"errors"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

func TestCompiledCLIExitCodesAreNotGoRunExitCodes(t *testing.T) {
	binary := filepath.Join(t.TempDir(), "promote-gate")
	if runtime.GOOS == "windows" {
		binary += ".exe"
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	if out, err := exec.CommandContext(ctx, goBinary(), "build", "-o", binary, ".").CombinedOutput(); err != nil {
		t.Fatalf("build: %v\n%s", err, out)
	}
	digest := "sha256:" + strings.Repeat("a", 64)
	cases := []struct {
		name string
		args []string
		code int
		text string
	}{
		{"allow", []string{"--digest", digest, "--revision", "abc1234", "--tests-passed=true", "--provenance-verified=true"}, 0, "promotion approved"},
		{"deny", []string{"--digest", digest, "--revision", "abc1234", "--tests-passed=true"}, 1, "promotion rejected: provenance not verified"},
		{"invalid", []string{"--digest", ":latest", "--revision", "abc1234"}, 2, "invalid candidate"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			out, err := exec.CommandContext(ctx, binary, tc.args...).CombinedOutput()
			code := 0
			if err != nil {
				var exit *exec.ExitError
				if !errors.As(err, &exit) {
					t.Fatalf("start: %v", err)
				}
				code = exit.ExitCode()
			}
			if code != tc.code || !strings.Contains(string(out), tc.text) {
				t.Fatalf("code=%d want=%d output=%s", code, tc.code, out)
			}
		})
	}
	out, err := exec.CommandContext(ctx, goBinary(), "run", ".", "--digest", ":latest", "--revision", "abc1234").CombinedOutput()
	var exit *exec.ExitError
	if !errors.As(err, &exit) || exit.ExitCode() != 1 || !strings.Contains(string(out), "exit status 2") {
		t.Fatalf("go run does not expose child status directly: %v\n%s", err, out)
	}
}
