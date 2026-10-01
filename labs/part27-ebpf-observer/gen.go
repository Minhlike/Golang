package ebpfobserver

// Generate bpf/vmlinux.h from the target Linux kernel's BTF before go generate.
// Clang's BPF target and libbpf headers are build-time prerequisites, not Go test prerequisites.
//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -target bpfel -cc clang bpf bpf/exec_observer.c -- -I./bpf -O2 -g
