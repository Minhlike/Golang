package main

import (
	"bytes"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func goBinary() string {
	return filepath.Join(runtime.GOROOT(), "bin", "go")
}

func TestCLIEvaluation(t *testing.T) {
	validDigest := "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
	goBin := goBinary()

	t.Run("approved", func(t *testing.T) {
		cmd := exec.Command(goBin, "run", ".",
			"--digest", validDigest,
			"--revision", "abc1234",
			"--tests-passed=true",
			"--provenance-verified=true",
		)
		var stdout, stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr
		err := cmd.Run()
		if err != nil {
			t.Fatalf("expected exit 0, got err: %v, stderr: %s", err, stderr.String())
		}
		if !strings.Contains(stdout.String(), "promotion approved") {
			t.Fatalf("unexpected stdout: %s", stdout.String())
		}
	})

	t.Run("rejected_tests_failed", func(t *testing.T) {
		cmd := exec.Command(goBin, "run", ".",
			"--digest", validDigest,
			"--revision", "abc1234",
			"--tests-passed=false",
			"--provenance-verified=true",
		)
		var stdout, stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr
		err := cmd.Run()
		if err == nil {
			t.Fatal("expected non-zero exit for rejected candidate")
		}
		if !strings.Contains(stderr.String(), "promotion rejected: tests not passed") {
			t.Fatalf("expected tests rejection reason in stderr, got: %s", stderr.String())
		}
	})

	t.Run("rejected_missing_provenance", func(t *testing.T) {
		cmd := exec.Command(goBin, "run", ".",
			"--digest", validDigest,
			"--revision", "abc1234",
			"--tests-passed=true",
			"--provenance-verified=false",
		)
		var stdout, stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr
		err := cmd.Run()
		if err == nil {
			t.Fatal("expected non-zero exit for missing provenance")
		}
		if !strings.Contains(stderr.String(), "promotion rejected: provenance not verified") {
			t.Fatalf("expected provenance rejection reason in stderr, got: %s", stderr.String())
		}
	})

	t.Run("malformed", func(t *testing.T) {
		cmd := exec.Command(goBin, "run", ".",
			"--digest", "bad-digest",
			"--revision", "abc1234",
		)
		var stdout, stderr bytes.Buffer
		cmd.Stdout = &stdout
		cmd.Stderr = &stderr
		err := cmd.Run()
		if err == nil {
			t.Fatal("expected non-zero exit for malformed candidate")
		}
		if !strings.Contains(stderr.String(), "invalid candidate") {
			t.Fatalf("expected invalid candidate in stderr, got: %s", stderr.String())
		}
	})
}
