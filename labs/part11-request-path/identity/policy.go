// Package identity is a local certificate-to-action teaching boundary.
package identity

import "net/http"

// Authorize trusts ONLY the verified leaf URI identity, never a caller header.
// One certificate must identify one principal. CA trust is not a role grant.
func Authorize(r *http.Request) bool {
	if r == nil || r.TLS == nil || len(r.TLS.VerifiedChains) == 0 ||
		len(r.TLS.VerifiedChains[0]) == 0 || r.TLS.VerifiedChains[0][0] == nil {
		return false
	}
	leaf := r.TLS.VerifiedChains[0][0]
	if len(leaf.URIs) != 1 {
		return false
	}
	principal := leaf.URIs[0].String()
	switch {
	case r.Method == http.MethodGet && r.URL.Path == "/read":
		return principal == "urn:go-book:reader" || principal == "urn:go-book:operator"
	case r.Method == http.MethodPost && r.URL.Path == "/write":
		return principal == "urn:go-book:operator"
	default:
		return false
	}
}
