package fixed

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"
)

var helperMode = flag.String("helper-mode", "", "mode for child-process test helper")

func TestHelperProcess(t *testing.T) {
	switch *helperMode {
	case "":
		return
	case "ok":
		fmt.Fprintln(os.Stdout, "ready")
		fmt.Fprintln(os.Stderr, "checked")
		os.Exit(0)
	case "fail":
		fmt.Fprintln(os.Stderr, "dependency refused")
		os.Exit(7)
	case "sleep":
		time.Sleep(5 * time.Second)
		os.Exit(0)
	default:
		os.Exit(99)
	}
}

func helperSpec(mode string, timeout time.Duration) Spec {
	return Spec{
		Name:    os.Args[0],
		Args:    []string{"-test.run=^TestHelperProcess$", "-helper-mode=" + mode},
		Timeout: timeout,
	}
}

func TestRunKeepsStreamsAndSuccessStatus(t *testing.T) {
	result, err := Run(context.Background(), helperSpec("ok", 5*time.Second))
	if err != nil {
		t.Fatalf("Run() error = %v", err)
	}
	if result.ExitCode != 0 || result.TimedOut {
		t.Fatalf("unexpected result: %#v", result)
	}
	if result.Stdout != "ready\n" || result.Stderr != "checked\n" {
		t.Fatalf("streams = stdout %q, stderr %q", result.Stdout, result.Stderr)
	}
}

func TestRunKeepsDiagnosticForNonZeroExit(t *testing.T) {
	result, err := Run(context.Background(), helperSpec("fail", 5*time.Second))
	var exitErr *exec.ExitError
	if !errors.As(err, &exitErr) {
		t.Fatalf("Run() error = %v, want wrapped *exec.ExitError", err)
	}
	if result.ExitCode != 7 || !strings.Contains(result.Stderr, "dependency refused") {
		t.Fatalf("unexpected result: %#v", result)
	}
}

func TestRunLabelsDeadline(t *testing.T) {
	result, err := Run(context.Background(), helperSpec("sleep", 30*time.Millisecond))
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("Run() error = %v, want DeadlineExceeded", err)
	}
	if !result.TimedOut {
		t.Fatalf("result = %#v, want TimedOut", result)
	}
}

func TestRunPreservesParentCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	result, err := Run(ctx, helperSpec("ok", 5*time.Second))
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("Run() error = %v, want Canceled", err)
	}
	if result.TimedOut {
		t.Fatalf("result = %#v, cancellation is not a timeout", result)
	}
}

func TestRunRejectsInvalidSpec(t *testing.T) {
	for _, spec := range []Spec{{}, {Name: os.Args[0]}} {
		if _, err := Run(context.Background(), spec); !errors.Is(err, ErrInvalidSpec) {
			t.Fatalf("Run(%#v) error = %v, want ErrInvalidSpec", spec, err)
		}
	}
}
