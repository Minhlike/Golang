package contracts

import (
	jsonv1 "encoding/json"
	jsonv2 "encoding/json/v2"
	"testing"
)

// These cases check default API behavior, not all JSON migration differences.
func TestJSONVersionBoundary(t *testing.T) {
	input := []byte(`{"port":80,"port":443}`)
	var dst struct{ Port int }
	if err := jsonv1.Unmarshal(input, &dst); err != nil || dst.Port != 443 {
		t.Fatalf("v1 duplicate name: port=%d err=%v", dst.Port, err)
	}
	if err := jsonv2.Unmarshal(input, &dst); err == nil {
		t.Fatal("v2 must reject duplicate names by default")
	}
	invalidUTF8 := []byte{'"', 0xff, '"'}
	var text string
	if err := jsonv1.Unmarshal(invalidUTF8, &text); err != nil || text != "\ufffd" {
		t.Fatalf("v1 invalid UTF-8 replacement: text=%q err=%v", text, err)
	}
	if err := jsonv2.Unmarshal(invalidUTF8, &text); err == nil {
		t.Fatal("v2 must reject invalid UTF-8 by default")
	}
}
