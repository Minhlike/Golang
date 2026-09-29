# Evidence before authority

Start with the requirements and `gate_test.go`, not `gate.go`. Move the reference
implementation aside in a scratch copy, define the public types, and implement
the contract from the tests. A valid request needs an authenticated operator,
an allowlisted local target, the one allowed action, a valid diff SHA-256, fresh
passing evidence bound to the plan digest, and unexpired approval for the same
caller and plan. Defaults deny.

The lab does not execute commands or access a real service. Evidence and approval
are trusted test inputs, not agent assertions. A digest detects mismatch, not
truth: production needs authenticated evidence and approval storage, immutable
artifacts, atomic checks with execution, replay controls and postcondition
observation. The test suite does not prove those absent mechanisms.

Run `go test -v ./...`, `go vet ./...`, `go test -race ./...`. Extend the contract
with a one-time approval in your own implementation; specify storage failure
and simultaneous consumers before deciding how a lock or transaction protects
it. Do not connect this exercise to production.
