# Contract probes for the encyclopedia edition

These small independent tests support Chapters 1, 3, 7, 8 and 14. Predict each
assertion before running `go test -v ./...`. The incompatible assignment under
`testdata` is deliberately invalid; a test compiles it and requires rejection.
Do not repair it to make the compiler happy.

For active practice, change one condition at a time: put an explicit type on the
first constant; replace the alias with a definition; remove the Scanner size
change; make Once retry after a recovered panic; or mutate the config after it
has been published. Explain which language/API contract changes and which test
is insufficient to prove a broader guarantee.

Run `go vet ./...` and `go test -race ./...`. The cgo package additionally needs
a supported C toolchain. It demonstrates C string length, not throughput or
pointer-retention safety. Its source is excluded with `CGO_ENABLED=0`; a
successful pure-Go cross-build therefore does not validate that package.

`TestWorkspaceSelectionIsNotPublishedDependency` creates two local modules:
workspace selection succeeds and the independent module build rejects the
undeclared dependency with network lookup disabled. Inspect `go list -json
./testdata/buildselect` under Windows and a Linux target; cross-build that fixture
with cgo disabled. Neither a successful build nor selected filename proves
target execution. This fixture supports only the two explicit OS targets.
