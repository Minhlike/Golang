package targets

import (
	"bufio"
	"bytes"
	"errors"
	"io"
	"io/fs"
	"math"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

type finalRead struct {
	data string
	err  error
}

func (r *finalRead) Read(p []byte) (int, error) {
	n := copy(p, r.data)
	r.data = r.data[n:]
	if r.data != "" {
		return n, nil
	}
	return n, r.err
}

func TestReadDataCanArriveWithEOFOrAnotherError(t *testing.T) {
	got, err := io.ReadAll(&finalRead{data: "last bytes", err: io.EOF})
	if string(got) != "last bytes" || err != nil {
		t.Fatalf("data + EOF: %q %v", got, err)
	}
	fault := errors.New("read fault")
	got, err = io.ReadAll(&finalRead{data: "partial", err: fault})
	if string(got) != "partial" || !errors.Is(err, fault) {
		t.Fatalf("data + error: %q %v", got, err)
	}
}

type countedReader struct{ calls int }

func (r *countedReader) Read([]byte) (int, error) {
	r.calls++
	return 0, io.EOF
}

func TestReadBoundedRejectsUnrepresentableProbeBeforeReading(t *testing.T) {
	for _, limit := range []int64{-1, math.MaxInt64} {
		r := &countedReader{}
		_, err := ReadBounded(r, limit)
		if err == nil || r.calls != 0 {
			t.Fatalf("limit=%d err=%v reads=%d", limit, err, r.calls)
		}
	}
	data, err := ReadBounded(strings.NewReader(""), 0)
	if err != nil || len(data) != 0 {
		t.Fatalf("empty zero limit: %q %v", data, err)
	}
	if _, err := ReadBounded(strings.NewReader("x"), 0); !errors.Is(err, ErrDocumentTooLarge) {
		t.Fatalf("nonempty zero limit: %v", err)
	}
}

type closeCounter struct {
	bytes.Buffer
	closed int
}

func (w *closeCounter) Close() error { w.closed++; return nil }

func TestClosingUnderlyingWriterDoesNotFlushBufio(t *testing.T) {
	w := &closeCounter{}
	b := bufio.NewWriter(w)
	if err := Encode(b, []Target{{Name: "billing"}}); err != nil {
		t.Fatal(err)
	}
	if err := w.Close(); err != nil || w.Len() != 0 || b.Buffered() == 0 {
		t.Fatal("closing underlying writer unexpectedly flushed bufio")
	}
	if err := b.Flush(); err != nil || !strings.Contains(w.String(), "billing") {
		t.Fatalf("explicit Flush: %v output=%q", err, w.String())
	}
	// This memory writer deliberately accepts bytes after Close. A real file
	// does not; the test demonstrates why Flush must precede closing a file.
}

func TestRealFilesystemRootConfinement(t *testing.T) {
	dir := t.TempDir()
	base := filepath.Join(dir, "root")
	if err := os.Mkdir(base, 0700); err != nil {
		t.Fatal(err)
	}
	for name, text := range map[string]string{"outside.txt": "outside", "root/inside.txt": "inside"} {
		if err := os.WriteFile(filepath.Join(dir, name), []byte(text), 0600); err != nil {
			t.Fatal(err)
		}
	}
	r, err := os.OpenRoot(base)
	if err != nil {
		t.Fatal(err)
	}
	defer r.Close()
	t.Run("dotdot traversal", func(t *testing.T) {
		if _, err := r.ReadFile("../outside.txt"); err == nil {
			t.Fatal("Root escaped via dotdot")
		}
		data, err := r.ReadFile("inside.txt")
		if err != nil || string(data) != "inside" {
			t.Fatalf("inside: %q %v", data, err)
		}
	})
	t.Run("real symlinks", func(t *testing.T) {
		if err := os.Symlink("../outside.txt", filepath.Join(base, "escape.txt")); err != nil {
			t.Skipf("SYMLINK_NOT_RUN: operating system prerequisite: %v", err)
		}
		if err := os.Symlink("inside.txt", filepath.Join(base, "local.txt")); err != nil {
			t.Fatal(err)
		}
		data, err := fs.ReadFile(os.DirFS(base), "escape.txt")
		if err != nil || string(data) != "outside" {
			t.Fatalf("DirFS: %q %v", data, err)
		}
		if _, err := r.ReadFile("escape.txt"); err == nil {
			t.Fatal("Root escaped via symlink")
		}
		data, err = r.ReadFile("local.txt")
		if err != nil || string(data) != "inside" {
			t.Fatalf("internal symlink: %q %v", data, err)
		}
	})
}
