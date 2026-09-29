package contracts

import (
	"bufio"
	"bytes"
	"embed"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
)

//go:embed fixtures/*.txt
var files embed.FS

type Port uint16
type PortAlias = uint16
type Named struct{ Name string }

func (n Named) Label() string { return n.Name }

type Embedded struct{ Named }

func TestConstantsAndIdentity(t *testing.T) {
	const (
		Pending = iota
		Running
		Stopped
	)
	const Reset = iota
	if Pending != 0 || Running != 1 || Stopped != 2 || Reset != 0 {
		t.Fatal("iota trace")
	}
	x := 500
	if reflect.TypeOf(x).Kind() != reflect.Int {
		t.Fatal("default integer type")
	}
	var alias PortAlias = 80
	var raw uint16 = alias
	if Port(raw) != 80 || (Embedded{Named{"api"}}).Label() != "api" {
		t.Fatal("conversion/promotion")
	}
	wide := uint32(65537)
	if Port(wide) != 1 {
		t.Fatal("conversion truncates; not domain validation")
	}
}

func TestDynamicComparabilityPanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Fatal("slice-backed interfaces must panic on equality")
		}
	}()
	var a, b any = []int{1}, []int{1}
	_ = a == b
}

func TestScannerLimitAndValidation(t *testing.T) {
	input := strings.Repeat("x", 128) + "\n"
	small := bufio.NewScanner(strings.NewReader(input))
	small.Buffer(make([]byte, 16), 64)
	if small.Scan() || small.Err() == nil {
		t.Fatal("oversized token accepted or error ignored")
	}
	large := bufio.NewScanner(strings.NewReader(input))
	large.Buffer(make([]byte, 16), 256)
	if !large.Scan() || len(large.Bytes()) != 128 || large.Scan() || large.Err() != nil {
		t.Fatal("bounded valid token")
	}
	if _, err := strconv.ParseUint("65536", 10, 16); err == nil {
		t.Fatal("overflow accepted")
	}
	if _, err := regexp.Compile("["); err == nil {
		t.Fatal("bad pattern accepted")
	}
}

func TestEmbeddedFSAndInvalidNames(t *testing.T) {
	data, err := fs.ReadFile(files, "fixtures/message.txt")
	if err != nil || !bytes.Equal(bytes.TrimSpace(data), []byte("built into the binary")) {
		t.Fatalf("embedded bytes: %q, %v", data, err)
	}
	if fs.ValidPath("../secret") || fs.ValidPath("/absolute") {
		t.Fatal("invalid logical names")
	}
}

func TestOncePanicIsNotRetry(t *testing.T) {
	var once sync.Once
	attempts := 0
	func() {
		defer func() { _ = recover() }()
		once.Do(func() { attempts++; panic("failed") })
	}()
	once.Do(func() { attempts++ })
	if attempts != 1 {
		t.Fatal("Once retried")
	}
}

func TestCondPredicateAndAtomicPublication(t *testing.T) {
	var mu sync.Mutex
	cond := sync.NewCond(&mu)
	ready := false
	done := make(chan struct{})
	go func() {
		mu.Lock()
		for !ready {
			cond.Wait()
		}
		mu.Unlock()
		close(done)
	}()
	mu.Lock()
	ready = true
	cond.Broadcast()
	mu.Unlock()
	<-done

	type Config struct{ Limit int }
	var current atomic.Pointer[Config]
	current.Store(&Config{Limit: 10})
	var workers sync.WaitGroup
	for range 16 {
		workers.Go(func() {
			for range 100 {
				if current.Load().Limit < 1 {
					t.Error("partial state")
				}
			}
		})
	}
	current.Store(&Config{Limit: 20}) // Neither published object is mutated.
	workers.Wait()
}

func TestCompilerRejectsIncompatibleDefinedTypes(t *testing.T) {
	cmd := exec.Command("go", "build", "-o", filepath.Join(t.TempDir(), "invalid"), "./testdata/incompatible")
	cmd.Env = append(os.Environ(), "GOWORK=off")
	if output, err := cmd.CombinedOutput(); err == nil || !strings.Contains(string(output), "cannot use") {
		t.Fatalf("expected compiler type failure: %v\n%s", err, output)
	}
}

func TestWorkspaceSelectionIsNotPublishedDependency(t *testing.T) {
	root := t.TempDir()
	fixtures := map[string]string{
		"a/go.mod": "module example.com/a\n\ngo 1.27.0\n",
		"a/a.go":   "package a\nimport \"example.com/b\"\nvar Value = b.Value\n",
		"b/go.mod": "module example.com/b\n\ngo 1.27.0\n",
		"b/b.go":   "package b\nconst Value = 1\n",
		"go.work":  "go 1.27.0\nuse (\n ./a\n ./b\n)\n",
	}
	for name, text := range fixtures {
		path := filepath.Join(root, name)
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, []byte(text), 0600); err != nil {
			t.Fatal(err)
		}
	}
	run := func(work string) error {
		cmd := exec.Command("go", "test", "./...")
		cmd.Dir = filepath.Join(root, "a")
		cmd.Env = append(os.Environ(), "GOWORK="+work, "GOPROXY=off", "GOSUMDB=off", "GOTOOLCHAIN=local")
		output, err := cmd.CombinedOutput()
		t.Logf("GOWORK=%s: %s", work, output)
		return err
	}
	if err := run(filepath.Join(root, "go.work")); err != nil {
		t.Fatal("workspace build", err)
	}
	if err := run("off"); err == nil {
		t.Fatal("undeclared dependency unexpectedly resolved")
	}
}
