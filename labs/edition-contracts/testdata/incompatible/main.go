package main

type Port uint16
type Attempts uint16

func main() {
	var port Port = 80
	var attempts Attempts = port // Intentional compiler rejection.
	_ = attempts
}
