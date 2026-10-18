package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestPointerAndMapRebindingStayLocal(t *testing.T) {
	x, other := 1, 2
	p := &x
	func(local *int) {
		*local = 7
		local = &other
		*local = 9
	}(p)
	if p != &x || x != 7 || other != 9 {
		t.Fatalf("pointer copy: p=%p x=%d other=%d", p, x, other)
	}
	m := map[string]int{"x": 1}
	func(local map[string]int) {
		local["x"] = 7
		local = map[string]int{"x": 9}
	}(m)
	if m["x"] != 7 {
		t.Fatalf("map rebinding changed caller: %v", m)
	}
}

func TestStructCopyDoesNotDeepCopyReachableData(t *testing.T) {
	type State struct {
		N     int
		Items []int
	}
	a := State{N: 1, Items: []int{1}}
	b := a
	b.N, b.Items[0] = 2, 3
	if a.N != 1 || a.Items[0] != 3 {
		t.Fatalf("copy contract: a=%+v b=%+v", a, b)
	}
	b.Items = []int{4}
	if a.Items[0] != 3 {
		t.Fatal("rebinding copied field changed original descriptor")
	}
}

func TestCompilerValueAndMethodBoundaries(t *testing.T) {
	cases := []struct {
		name, body, diagnostic string
	}{
		{"composite-not-constant", `const s = Service{}`, "is not constant"},
		{"map-field-not-assignable", `m := map[string]Service{}; m["x"].Healthy = false`, "cannot assign"},
		{"map-element-not-addressable", `m := map[string]Service{}; _ = &m["x"]`, "cannot take address"},
		{"map-pointer-method", `m := map[string]Service{}; m["x"].Record(false)`, "cannot call pointer method"},
		{"value-interface", `var _ Recorder = Service{}`, "pointer receiver"},
		{"defined-types", `type Port uint16; type Attempts uint16; var p Port; var _ Attempts = p`, "cannot use"},
		{"constant-overflow", `type Port uint16; _ = Port(65537)`, "overflows"},
		{"allowed-forms", `p := &Service{}; p.Healthy = true; var _ Recorder = p; type Box struct{ N int }; var b Box; var _ struct{ N int } = b; type Alias = uint16; var a Alias; var _ uint16 = a`, ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			dir := t.TempDir()
			source := "package main\ntype Service struct{ Healthy bool }\n" +
				"func (*Service) Record(bool){}\ntype Recorder interface{ Record(bool) }\n" +
				"func main(){" + tc.body + "}\n"
			path := filepath.Join(dir, "main.go")
			if err := os.WriteFile(path, []byte(source), 0600); err != nil {
				t.Fatal(err)
			}
			cmd := exec.Command("go", "build", "-o", filepath.Join(dir, "program.exe"), path)
			cmd.Env = append(os.Environ(), "GOWORK=off", "GOTOOLCHAIN=local", "GOPROXY=off")
			output, err := cmd.CombinedOutput()
			if tc.diagnostic == "" {
				if err != nil {
					t.Fatalf("valid source rejected: %v\n%s", err, output)
				}
			} else if err == nil || !strings.Contains(string(output), tc.diagnostic) {
				t.Fatalf("want rejection %q: %v\n%s", tc.diagnostic, err, output)
			}
			t.Logf("accept=%t compiler output=%s", err == nil, output)
		})
	}
}
