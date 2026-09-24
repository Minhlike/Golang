package ebpfobserver

import (
	"context"
	"errors"
	"io"
	"strings"
	"sync"
)

var (
	ErrObserverClosed = errors.New("observer already closed")
)

// RecordReader abstracts binary event acquisition from the BPF ring buffer.
type RecordReader interface {
	Read() ([]byte, error)
	Close() error
}

// Observer coordinates kernel event streaming into userspace Go channels.
type Observer struct {
	reader RecordReader
	events chan *ExecEvent
	errs   chan error
	done   chan struct{}
	closeOnce sync.Once
}

// NewObserver instantiates a stream observer with buffered channels.
func NewObserver(reader RecordReader, bufferSize int) *Observer {
	if bufferSize <= 0 {
		bufferSize = 128
	}
	return &Observer{
		reader: reader,
		events: make(chan *ExecEvent, bufferSize),
		errs:   make(chan error, 16),
		done:   make(chan struct{}),
	}
}

// Start begins processing events asynchronously until context is canceled or reader closes.
func (o *Observer) Start(ctx context.Context) (<-chan *ExecEvent, <-chan error) {
	go func() {
		defer close(o.events)
		defer close(o.errs)

		for {
			select {
			case <-ctx.Done():
				return
			case <-o.done:
				return
			default:
				data, err := o.reader.Read()
				if err != nil {
					if errors.Is(err, io.EOF) || errors.Is(err, ErrObserverClosed) {
						return
					}
					select {
					case o.errs <- err:
					case <-ctx.Done():
						return
					case <-o.done:
						return
					}
					continue
				}

				event, decodeErr := DecodeExecEvent(data)
				if decodeErr != nil {
					select {
					case o.errs <- decodeErr:
					case <-ctx.Done():
						return
					case <-o.done:
						return
					}
					continue
				}

				select {
				case o.events <- event:
				case <-ctx.Done():
					return
				case <-o.done:
					return
				}
			}
		}
	}()

	return o.events, o.errs
}

// Close stops observation and releases kernel or memory resources.
func (o *Observer) Close() error {
	var err error
	o.closeOnce.Do(func() {
		close(o.done)
		if o.reader != nil {
			err = o.reader.Close()
		}
	})
	return err
}

// SecurityAlert represents a policy violation or suspicious behavior detected in kernel space.
type SecurityAlert struct {
	Event  *ExecEvent
	Rule   string
	Reason string
}

// DetectSecurityAnomalies analyzes observed process execution against zero-trust rules.
func DetectSecurityAnomalies(e *ExecEvent) *SecurityAlert {
	if e == nil {
		return nil
	}

	fn := strings.ToLower(e.Filename)
	comm := strings.ToLower(e.Comm)

	// Rule 1: Execution from suspicious world-writable paths (/tmp, /dev/shm, /var/tmp)
	if strings.HasPrefix(fn, "/tmp/") || strings.HasPrefix(fn, "/dev/shm/") || strings.HasPrefix(fn, "/var/tmp/") {
		return &SecurityAlert{
			Event:  e,
			Rule:   "SEC01_EXEC_FROM_TEMP_DIRECTORY",
			Reason: "process execution originated from world-writable temporary directory",
		}
	}

	// Rule 2: Shell execution spawned by application runtime / webserver (Potential RCE)
	isShell := fn == "/bin/sh" || fn == "/bin/bash" || fn == "/usr/bin/bash" || fn == "/bin/dash"
	isWebWorker := comm == "nginx" || comm == "node" || comm == "python" || comm == "redis-server"
	if isShell && isWebWorker {
		return &SecurityAlert{
			Event:  e,
			Rule:   "SEC02_SHELL_FROM_WEBSERVER",
			Reason: "interactive shell spawned directly from web service daemon process",
		}
	}

	// Rule 3: Network recon / reverse shell tools (nc, ncat, nmap) executed as root (UID 0)
	isNetTool := strings.HasSuffix(fn, "/nc") || strings.HasSuffix(fn, "/ncat") || strings.HasSuffix(fn, "/nmap")
	if isNetTool && e.UID == 0 {
		return &SecurityAlert{
			Event:  e,
			Rule:   "SEC03_ROOT_NETWORK_RECON",
			Reason: "network exploration utility executed with root privileges",
		}
	}

	return nil
}
