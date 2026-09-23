package main

import (
	"flag"
	"fmt"
	"os"

	"example.com/golang-master/part18-workflow-delivery/gate"
)

func main() {
	digest := flag.String("digest", "", "immutable image digest (e.g. sha256:...)")
	revision := flag.String("revision", "", "source git revision (commit SHA)")
	testsPassed := flag.Bool("tests-passed", false, "whether test suite passed")
	provenanceVerified := flag.Bool("provenance-verified", false, "whether provenance attestation verified")
	flag.Parse()

	candidate := gate.Candidate{
		Digest:             *digest,
		Revision:           *revision,
		TestsPassed:        *testsPassed,
		ProvenanceVerified: *provenanceVerified,
	}

	decision, err := gate.Evaluate(candidate)
	if err != nil {
		fmt.Fprintf(os.Stderr, "invalid candidate: %v\n", err)
		os.Exit(2)
	}

	if !decision.Allowed {
		fmt.Fprintf(os.Stderr, "promotion rejected: %s\n", decision.Reason)
		os.Exit(1)
	}

	fmt.Printf("promotion approved: digest=%s revision=%s\n", decision.Digest, candidate.Revision)
}
