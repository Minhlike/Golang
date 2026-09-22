package fixed

import (
	"runtime"
	"testing"
	"unsafe"
)

type Header struct {
	Flag byte
	ID   uint64
}

func TestHeaderLayoutMeasurement(t *testing.T) {
	t.Logf(
		"Go=%s GOOS=%s GOARCH=%s size=%d align=%d id-offset=%d",
		runtime.Version(),
		runtime.GOOS,
		runtime.GOARCH,
		unsafe.Sizeof(Header{}),
		unsafe.Alignof(Header{}),
		unsafe.Offsetof(Header{}.ID),
	)
}
