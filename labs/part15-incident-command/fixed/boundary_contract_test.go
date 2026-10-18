package fixed

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"reflect"
	"testing"
	"time"
)

var contractMode = flag.String("contract-mode", "", "child helper for command boundary tests")

func TestContractChild(t *testing.T) {
	switch *contractMode {
	case "":
		return
	case "argv":
		if err := json.NewEncoder(os.Stdout).Encode(flag.Args()); err != nil {
			os.Exit(98)
		}
		os.Exit(0)
	case "gate":
		conn, err := net.DialTimeout("tcp", flag.Arg(0), 10*time.Second)
		if err != nil {
			os.Exit(97)
		}
		if _, err := fmt.Fprintln(conn, "ready"); err != nil {
			os.Exit(96)
		}
		_, _ = io.Copy(io.Discard, conn)
		_ = conn.Close()
		os.Exit(0)
	default:
		os.Exit(99)
	}
}

func TestRunPreservesLiteralArguments(t *testing.T) {
	want := []string{"a b", "x;y", "*", "$HOME", "--unsafe-option", ""}
	args := append([]string{"-test.run=^TestContractChild$", "-contract-mode=argv", "--"}, want...)
	spec := Spec{Name: os.Args[0], Args: args, Timeout: 10 * time.Second}
	result, err := Run(context.Background(), spec)
	if err != nil {
		t.Fatal(err)
	}
	var got []string
	if err := json.Unmarshal([]byte(result.Stdout), &got); err != nil || !reflect.DeepEqual(got, want) {
		t.Fatalf("argv changed: got=%q want=%q decode=%v", got, want, err)
	}
	args[0] = "mutated after return"
	if result.Command[1] == args[0] {
		t.Fatal("Result.Command must own its argument snapshot")
	}
}

func TestRunInvalidAndMissingExecutableAreDifferent(t *testing.T) {
	result, err := Run(nil, Spec{Name: os.Args[0], Timeout: time.Second})
	if !errors.Is(err, ErrInvalidSpec) || len(result.Command) != 0 || result.ExitCode != 0 {
		t.Fatalf("invalid spec returns zero Result, not proof of exit0: %#v %v", result, err)
	}
	name := filepath.Join(t.TempDir(), "does-not-exist.exe")
	result, err = Run(context.Background(), Spec{Name: name, Timeout: 10 * time.Second})
	if err == nil || errors.Is(err, ErrInvalidSpec) || result.ExitCode != -1 || len(result.Command) != 1 || result.Command[0] != name || result.TimedOut {
		t.Fatalf("start failure contract: %#v %v", result, err)
	}
}

func TestRunCancelsAnAlreadyStartedChild(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer listener.Close()
	_ = listener.(*net.TCPListener).SetDeadline(time.Now().Add(10 * time.Second))
	ctx, cancel := context.WithCancel(context.Background())
	type outcome struct {
		result Result
		err    error
	}
	done := make(chan outcome, 1)
	go func() {
		result, err := Run(ctx, Spec{Name: os.Args[0], Args: []string{"-test.run=^TestContractChild$", "-contract-mode=gate", "--", listener.Addr().String()}, Timeout: 20 * time.Second})
		done <- outcome{result, err}
	}()
	joined := false
	defer func() {
		cancel()
		if !joined {
			select {
			case <-done:
			case <-time.After(30 * time.Second):
				t.Error("runner did not join during cleanup")
			}
		}
	}()
	conn, err := listener.Accept()
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	_ = conn.SetReadDeadline(time.Now().Add(10 * time.Second))
	ready := make([]byte, len("ready\n"))
	if _, err := io.ReadFull(conn, ready); err != nil || string(ready) != "ready\n" {
		t.Fatalf("child did not acknowledge start: %q %v", ready, err)
	}
	cancel()
	select {
	case got := <-done:
		joined = true
		if !errors.Is(got.err, context.Canceled) || got.result.TimedOut {
			t.Fatalf("started child cancellation: %#v %v", got.result, got.err)
		}
	case <-time.After(30 * time.Second):
		t.Fatal("runner failed to return after cancellation")
	}
	if n, err := conn.Read(make([]byte, 1)); n != 0 || err == nil {
		t.Fatalf("child connection is still open: n=%d err=%v", n, err)
	} else if timeout, ok := err.(net.Error); ok && timeout.Timeout() {
		t.Fatalf("connection did not close before guard deadline: %v", err)
	}
}
