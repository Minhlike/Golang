package main

import "fmt"

const service = "checkout"

func severity(status int) string {
	switch {
	case status >= 500:
		return "critical"
	case status >= 400:
		return "warning"
	default:
		return "normal"
	}
}

func main() {
	statuses := []int{200, 503, 404}
	for _, status := range statuses {
		fmt.Println(service, status, severity(status))
	}
}
