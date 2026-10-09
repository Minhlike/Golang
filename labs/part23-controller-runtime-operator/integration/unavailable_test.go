//go:build integration && !linux

package integration

import "testing"

func TestRealAPIContract(t *testing.T) {
	t.Skip("NOT_RUN: pinned envtest requires Linux; run with Kubernetes 1.37.x assets in WSL/Linux")
}
