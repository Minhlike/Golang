// Package status classifies a probe latency with explicit threshold rules.
package status

// ClassifyLatency returns the status for a latency measured in milliseconds.
func ClassifyLatency(latencyMS int) string {
	switch {
	case latencyMS < 0:
		return "invalid"
	case latencyMS < 200:
		return "healthy"
	case latencyMS < 1000:
		return "degraded"
	default:
		return "unhealthy"
	}
}
