//go:build cgo

package interop

/*
#include <stdlib.h>
#include <string.h>
*/
import "C"

import "unsafe"

// Length measures bytes before the first NUL, as required by C strlen.
func Length(s string) int {
	p := C.CString(s)
	defer C.free(unsafe.Pointer(p))
	return int(C.strlen(p))
}
