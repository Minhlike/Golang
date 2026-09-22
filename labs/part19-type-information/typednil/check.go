package typednil

type ProbeError struct {
	Target string
}

func (err *ProbeError) Error() string {
	return "probe failed: " + err.Target
}

// Check has an intentional typed-nil bug for the exercise.
func Check(ok bool) error {
	var problem *ProbeError
	if !ok {
		problem = &ProbeError{Target: "api"}
	}
	return problem
}
