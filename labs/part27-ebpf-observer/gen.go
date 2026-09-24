package ebpfobserver

//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -target bpfel -cc clang bpf bpf/exec_observer.c -- -I/usr/include/bpf -O2 -g
