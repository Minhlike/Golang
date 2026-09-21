package baseline

import "strconv"

// Reading is one endpoint measurement rendered by the case study.
type Reading struct {
	Name   string
	Millis int64
}

// Render keeps the same wire format as fixed.Render but intentionally creates
// intermediate strings, so the profiling exercise has a concrete baseline.
func Render(readings []Reading) string {
	var out string
	for _, reading := range readings {
		out += reading.Name + "=" + strconv.FormatInt(reading.Millis, 10) + "ms\n"
	}
	return out
}
