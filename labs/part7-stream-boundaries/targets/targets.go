// Package targets decodes and writes a small, single-document target config.
package targets

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
)

// Target is one named endpoint in a target config document.
type Target struct {
	Name     string `json:"name"`
	Endpoint string `json:"endpoint"`
}

// Decode accepts exactly one JSON document from r.
func Decode(r io.Reader) ([]Target, error) {
	dec := json.NewDecoder(r)
	var targets []Target
	if err := dec.Decode(&targets); err != nil {
		return nil, fmt.Errorf("decode target document: %w", err)
	}

	var extra any
	if err := dec.Decode(&extra); !errors.Is(err, io.EOF) {
		if err == nil {
			return nil, errors.New("target config must contain one JSON value")
		}
		return nil, fmt.Errorf("read after target document: %w", err)
	}
	return targets, nil
}

// Encode writes targets as one JSON document followed by a newline.
func Encode(w io.Writer, targets []Target) error {
	if err := json.NewEncoder(w).Encode(targets); err != nil {
		return fmt.Errorf("encode target document: %w", err)
	}
	return nil
}

// Save opens an output, writes one document, and preserves the first failure.
func Save(open func() (io.WriteCloser, error), targets []Target) (err error) {
	w, err := open()
	if err != nil {
		return fmt.Errorf("open target output: %w", err)
	}
	defer func() {
		if closeErr := w.Close(); err == nil && closeErr != nil {
			err = fmt.Errorf("close target output: %w", closeErr)
		}
	}()
	return Encode(w, targets)
}
