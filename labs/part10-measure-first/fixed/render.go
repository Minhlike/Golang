package fixed

import (
	"strconv"
	"strings"
)

type Reading struct {
	Name   string
	Millis int64
}

func Render(readings []Reading) string {
	var out strings.Builder
	for _, reading := range readings {
		out.WriteString(reading.Name)
		out.WriteByte('=')
		out.WriteString(strconv.FormatInt(reading.Millis, 10))
		out.WriteString("ms\n")
	}
	return out.String()
}
