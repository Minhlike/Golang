package main

import "fmt"

func redactedCopy(fields []string) []string {
	preview := make([]string, len(fields))
	copy(preview, fields)
	preview[0] = "***"
	return preview
}

func main() {
	a := []int{10, 20, 30}
	b := a
	b[0] = 99
	fmt.Println(a)
	fmt.Println(b)

	text := "Việt"
	fmt.Println(len(text))
	for index, value := range text {
		fmt.Println(index, value)
	}
}
