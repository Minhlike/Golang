package main

import (
	"bytes"
	"context"
	"strings"
	"testing"

	"example.com/golang-master/part6-testable-command/probe"
)

func TestRunWritesSuccessContract(t *testing.T) {
	var out, errOut bytes.Buffer
	code := run(context.Background(), &out, &errOut, func(string) (string, bool) { return "", false }, func(context.Context, probe.Endpoint) error { return nil })
	if code != 0 || out.String() != "billing healthy=true\n" || errOut.Len() != 0 {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, out.String(), errOut.String())
	}
}

func TestRunWritesConfigurationFailureContract(t *testing.T) {
	var out, errOut bytes.Buffer
	code := run(context.Background(), &out, &errOut, func(string) (string, bool) { return "payments.internal:0", true }, func(context.Context, probe.Endpoint) error { t.Fatal("runner called"); return nil })
	if code != 2 || out.Len() != 0 || !strings.Contains(errOut.String(), "outside 1..65535") {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, out.String(), errOut.String())
	}
}
