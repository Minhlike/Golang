package fixed

import (
	"errors"
	"reflect"
	"testing"
	"unsafe"
)

func TestReflectPermissionsAndShallowCopy(t *testing.T) {
	config := struct{ secret string }{secret: "keep"}
	field := reflect.ValueOf(&config).Elem().Field(0)
	if !field.CanAddr() || field.CanSet() || field.CanInterface() {
		t.Fatalf("private field permissions: addr=%v set=%v interface=%v", field.CanAddr(), field.CanSet(), field.CanInterface())
	}
	items := []string{"before"}
	value := reflect.ValueOf(items)
	if value.CanSet() || !value.Index(0).CanSet() {
		t.Fatal("slice container and element have different setter permissions")
	}
	value.Index(0).SetString("after")
	if items[0] != "after" {
		t.Fatal("interface copy must still share the slice backing array")
	}
	if reflect.ValueOf(nil).IsValid() {
		t.Fatal("nil interface must give an invalid Value")
	}
	var pointer *Config
	v := reflect.ValueOf(pointer)
	if !v.IsValid() || v.Kind() != reflect.Pointer || !v.IsNil() || v.Elem().IsValid() {
		t.Fatal("typed nil pointer differs from invalid Value")
	}
}

func TestApplyEnvExactAliasAndSchemaWithoutValues(t *testing.T) {
	type Text = string
	config := struct {
		Name Text `env:"NAME"`
	}{}
	if err := ApplyEnv(&config, map[string]string{"NAME": "set"}); err != nil || config.Name != "set" {
		t.Fatalf("alias must retain exact string identity: value=%q err=%v", config.Name, err)
	}
	bad := struct {
		Name  string `env:"NAME"`
		Count int    `env:"COUNT"`
	}{Name: "keep"}
	if err := ApplyEnv(&bad, map[string]string{"NAME": "replace"}); !errors.Is(err, ErrSchema) || bad.Name != "keep" {
		t.Fatalf("missing COUNT must not hide an invalid schema: value=%q err=%v", bad.Name, err)
	}
}

func TestUnsafeHelpersEmptyAndSharedStorage(t *testing.T) {
	if got := unsafe.String(unsafe.StringData(""), 0); got != "" {
		t.Fatalf("empty string = %q", got)
	}
	var absent []byte
	if unsafe.SliceData(absent) != nil || unsafe.Slice(unsafe.SliceData(absent), 0) != nil {
		t.Fatal("nil slice must retain nil at length zero")
	}
	empty := make([]byte, 0)
	if ptr := unsafe.SliceData(empty); ptr == nil || len(unsafe.Slice(ptr, 0)) != 0 {
		t.Fatal("non-nil zero-capacity slice gives non-nil unspecified pointer, not readable bytes")
	}
	buf := []byte("go")
	view := unsafe.Slice(unsafe.SliceData(buf), len(buf))
	view[0] = 'G'
	if string(buf) != "Go" {
		t.Fatal("unsafe.Slice is a shared view, not a copy")
	}
}
