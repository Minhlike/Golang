package ebpfobserver

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"time"
)

// EventPayloadSize represents the exact C struct size (160 bytes).
const EventPayloadSize = 160

// ExecEvent models the structured information observed from Linux kernel execve.
type ExecEvent struct {
	PID       uint32    `json:"pid"`
	PPID      uint32    `json:"ppid"`
	UID       uint32    `json:"uid"`
	GID       uint32    `json:"gid"`
	Comm      string    `json:"comm"`
	Filename  string    `json:"filename"`
	Timestamp time.Time `json:"timestamp"`
}

// DecodeExecEvent deserializes raw little-endian binary bytes from the eBPF ring buffer.
func DecodeExecEvent(data []byte) (*ExecEvent, error) {
	if len(data) < EventPayloadSize {
		return nil, fmt.Errorf(
			"truncated event payload: expected at least %d bytes, got %d",
			EventPayloadSize, len(data),
		)
	}

	pid := binary.LittleEndian.Uint32(data[0:4])
	ppid := binary.LittleEndian.Uint32(data[4:8])
	uid := binary.LittleEndian.Uint32(data[8:12])
	gid := binary.LittleEndian.Uint32(data[12:16])

	commBytes := data[16:32]
	fileBytes := data[32:160]

	return &ExecEvent{
		PID:       pid,
		PPID:      ppid,
		UID:       uid,
		GID:       gid,
		Comm:      parseCString(commBytes),
		Filename:  parseCString(fileBytes),
		Timestamp: time.Now().UTC(),
	}, nil
}

// EncodeExecEvent serializes an ExecEvent into the exact 160-byte C struct ABI layout.
func EncodeExecEvent(e *ExecEvent) ([]byte, error) {
	if e == nil {
		return nil, errors.New("cannot encode nil ExecEvent")
	}

	buf := make([]byte, EventPayloadSize)
	binary.LittleEndian.PutUint32(buf[0:4], e.PID)
	binary.LittleEndian.PutUint32(buf[4:8], e.PPID)
	binary.LittleEndian.PutUint32(buf[8:12], e.UID)
	binary.LittleEndian.PutUint32(buf[12:16], e.GID)

	copy(buf[16:32], e.Comm)
	copy(buf[32:160], e.Filename)

	return buf, nil
}

// parseCString trims trailing null bytes from C char arrays.
func parseCString(b []byte) string {
	idx := bytes.IndexByte(b, 0)
	if idx >= 0 {
		return string(b[:idx])
	}
	return string(b)
}
