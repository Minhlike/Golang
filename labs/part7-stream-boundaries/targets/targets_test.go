package targets

import (
	"bytes"
	"errors"
	"io"
	"reflect"
	"strings"
	"testing"
)

func TestDecodeConsumesChunkedStream(t *testing.T) {
	r := &chunkReader{remaining: `[{"name":"billing","endpoint":"https://billing.internal/health"}]`, chunkSize: 3}

	got, err := Decode(r)
	if err != nil {
		t.Fatalf("Decode() error = %v", err)
	}
	want := []Target{{Name: "billing", Endpoint: "https://billing.internal/health"}}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("Decode() = %#v, want %#v", got, want)
	}
}

func TestDecodeRejectsAdditionalDocument(t *testing.T) {
	_, err := Decode(strings.NewReader(`[] {"not":"a target document"}`))
	if err == nil || !strings.Contains(err.Error(), "one JSON value") {
		t.Fatalf("Decode() error = %v, want additional-document error", err)
	}
}

func TestReadBoundedKeepsInputAtLimit(t *testing.T) {
	got, err := ReadBounded(strings.NewReader("12345"), 5)
	if err != nil {
		t.Fatalf("ReadBounded() error = %v", err)
	}
	if string(got) != "12345" {
		t.Fatalf("ReadBounded() = %q", got)
	}
}

func TestReadBoundedRejectsInputOverLimit(t *testing.T) {
	_, err := ReadBounded(strings.NewReader("123456"), 5)
	if !errors.Is(err, ErrDocumentTooLarge) {
		t.Fatalf("ReadBounded() error = %v, want ErrDocumentTooLarge", err)
	}
}

func TestSaveReturnsCloseError(t *testing.T) {
	closeErr := errors.New("flush failed")
	w := &closeFailWriter{closeErr: closeErr}

	err := Save(func() (io.WriteCloser, error) { return w, nil }, []Target{{Name: "billing"}})
	if !errors.Is(err, closeErr) {
		t.Fatalf("Save() error = %v, want close error", err)
	}
	if !strings.Contains(w.String(), `"name":"billing"`) {
		t.Fatalf("Save() output = %q", w.String())
	}
}

func TestSavePreservesWriteError(t *testing.T) {
	writeErr := errors.New("disk full")
	w := &writeFailWriter{writeErr: writeErr, closeErr: errors.New("flush failed")}

	err := Save(func() (io.WriteCloser, error) { return w, nil }, []Target{{Name: "billing"}})
	if !errors.Is(err, writeErr) {
		t.Fatalf("Save() error = %v, want write error", err)
	}
}

type chunkReader struct {
	remaining string
	chunkSize int
}

func (r *chunkReader) Read(p []byte) (int, error) {
	if r.remaining == "" {
		return 0, io.EOF
	}
	n := r.chunkSize
	if n > len(p) {
		n = len(p)
	}
	if n > len(r.remaining) {
		n = len(r.remaining)
	}
	copy(p, r.remaining[:n])
	r.remaining = r.remaining[n:]
	return n, nil
}

type closeFailWriter struct {
	bytes.Buffer
	closeErr error
}

func (w *closeFailWriter) Close() error {
	return w.closeErr
}

type writeFailWriter struct {
	writeErr error
	closeErr error
}

func (w *writeFailWriter) Write([]byte) (int, error) {
	return 0, w.writeErr
}

func (w *writeFailWriter) Close() error {
	return w.closeErr
}
