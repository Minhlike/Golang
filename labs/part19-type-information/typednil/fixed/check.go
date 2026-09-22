package fixed

type ProbeError struct {
	Target string
}

func (err *ProbeError) Error() string {
	return "probe failed: " + err.Target
}

func Check(ok bool) error {
	if ok {
		return nil
	}
	return &ProbeError{Target: "api"}
}
