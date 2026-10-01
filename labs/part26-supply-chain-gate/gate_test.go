package supplychain

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"errors"
	"testing"
)

type verifierFunc struct {
	verify func(string, *Attestation) error
}

func (v verifierFunc) VerifyProvenance(digest string, att *Attestation) error {
	return v.verify(digest, att)
}

func generateTestKeyPair(t *testing.T) (*ecdsa.PrivateKey, *ecdsa.PublicKey) {
	priv, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatalf("failed to generate ecdsa key: %v", err)
	}
	return priv, &priv.PublicKey
}

func signDigest(t *testing.T, priv *ecdsa.PrivateKey, digest string) []byte {
	h := sha256.Sum256([]byte(digest))
	sig, err := ecdsa.SignASN1(rand.Reader, priv, h[:])
	if err != nil {
		t.Fatalf("failed to sign digest: %v", err)
	}
	return sig
}

func TestPolicyGateAllowedWithValidSignature(t *testing.T) {
	trustedBuilder := "https://github.com/my-org/repo/.github/workflows/build.yml@refs/heads/main"
	trustedIssuer := "https://token.actions.githubusercontent.com"
	engine := NewPolicyEngine([]string{trustedBuilder}, []string{trustedIssuer})

	priv, pub := generateTestKeyPair(t)
	digest := ComputeContentDigest([]byte("container-image-binary-content-v1"))

	sig := &SignatureVerification{
		PublicKey: pub,
		Signature: signDigest(t, priv, digest),
		Issuer:    trustedIssuer,
	}

	att := &Attestation{
		BuilderID:     trustedBuilder,
		SubjectDigest: digest,
	}

	res := engine.Evaluate(digest, sig, att, nil)
	if res.Decision != DecisionAllow {
		t.Fatalf("expected DecisionAllow, got %s: %v", res.Decision, res.Violations)
	}
	if len(res.Violations) > 0 {
		t.Errorf("expected 0 violations, got %d", len(res.Violations))
	}
}

// This is an evidence-boundary test, not a production authorization guarantee.
// A model ALLOW cannot establish the signer or builder's authenticated identity.
func TestModelDoesNotAuthenticateSelfAssertedIdentity(t *testing.T) {
	issuer := "https://token.actions.githubusercontent.com"
	builder := "https://github.com/allowed/repo/build"
	engine := NewPolicyEngine([]string{builder}, []string{issuer})
	callerKey, callerPublic := generateTestKeyPair(t)
	digest := ComputeContentDigest([]byte("caller-created-content"))
	sig := &SignatureVerification{
		PublicKey: callerPublic,
		Signature: signDigest(t, callerKey, digest),
		Issuer:    issuer, // Just a label; no OIDC issuer was contacted.
	}
	att := &Attestation{BuilderID: builder, SubjectDigest: digest}
	result := engine.Evaluate(digest, sig, att, nil)
	if result.Decision != DecisionAllow {
		t.Fatalf("model boundary changed: got %s", result.Decision)
	}
}

func TestPolicyGateDenyUnsignedImage(t *testing.T) {
	trustedBuilder := "https://github.com/my-org/repo/.github/workflows/build.yml@refs/heads/main"
	trustedIssuer := "https://token.actions.githubusercontent.com"
	engine := NewPolicyEngine([]string{trustedBuilder}, []string{trustedIssuer})

	digest := ComputeContentDigest([]byte("unsigned-container-image"))
	att := &Attestation{
		BuilderID:     trustedBuilder,
		SubjectDigest: digest,
	}

	res := engine.Evaluate(digest, nil, att, nil)
	if res.Decision != DecisionDeny {
		t.Fatalf("expected DecisionDeny for unsigned image, got %s", res.Decision)
	}
}

func TestPolicyGateDenyReachableVulnerability(t *testing.T) {
	trustedBuilder := "https://github.com/my-org/repo/.github/workflows/build.yml@refs/heads/main"
	trustedIssuer := "https://token.actions.githubusercontent.com"
	engine := NewPolicyEngine([]string{trustedBuilder}, []string{trustedIssuer})

	priv, pub := generateTestKeyPair(t)
	digest := ComputeContentDigest([]byte("vuln-image"))

	sig := &SignatureVerification{
		PublicKey: pub,
		Signature: signDigest(t, priv, digest),
		Issuer:    trustedIssuer,
	}

	att := &Attestation{
		BuilderID:     trustedBuilder,
		SubjectDigest: digest,
	}

	vulns := []Vulnerability{
		{
			ID:        "GO-2026-9999",
			Package:   "golang.org/x/crypto",
			Symbol:    "ssh.ParsePrivateKey",
			Severity:  "CRITICAL",
			Reachable: true, // Reachable in binary call-graph!
		},
	}

	res := engine.Evaluate(digest, sig, att, vulns)
	if res.Decision != DecisionDeny {
		t.Fatalf("expected DecisionDeny for reachable critical vuln, got %s", res.Decision)
	}
	if len(res.Violations) == 0 {
		t.Errorf("expected violation recorded for reachable vuln")
	}
}

func TestPolicyGateAllowUncalledVulnerability(t *testing.T) {
	trustedBuilder := "https://github.com/my-org/repo/.github/workflows/build.yml@refs/heads/main"
	trustedIssuer := "https://token.actions.githubusercontent.com"
	engine := NewPolicyEngine([]string{trustedBuilder}, []string{trustedIssuer})

	priv, pub := generateTestKeyPair(t)
	digest := ComputeContentDigest([]byte("uncalled-vuln-image"))

	sig := &SignatureVerification{
		PublicKey: pub,
		Signature: signDigest(t, priv, digest),
		Issuer:    trustedIssuer,
	}

	att := &Attestation{
		BuilderID:     trustedBuilder,
		SubjectDigest: digest,
	}

	vulns := []Vulnerability{
		{
			ID:        "GO-2026-1111",
			Package:   "golang.org/x/net",
			Symbol:    "http2.Server.ServeConn",
			Severity:  "HIGH",
			Reachable: false, // In dependency graph, but symbol is uncalled
		},
	}

	res := engine.Evaluate(digest, sig, att, vulns)
	if res.Decision != DecisionAllow {
		t.Fatalf("expected DecisionAllow for uncalled vulnerability, got %s", res.Decision)
	}
	if len(res.Warnings) != 1 {
		t.Errorf("expected 1 audit warning for tolerated uncalled vuln, got %d", len(res.Warnings))
	}
}

func TestPolicyGateFailClosedOnMutableTag(t *testing.T) {
	engine := NewPolicyEngine(nil, nil)

	// Passing a mutable tag instead of sha256 content-addressed digest
	res := engine.Evaluate("my-registry.io/app:v1.2.0", nil, nil, nil)
	if res.Decision != DecisionDeny {
		t.Fatalf("expected DecisionDeny on mutable tag, got %s", res.Decision)
	}
}

func TestPolicyGateStopsBeforeProvenanceAfterSignatureFailure(t *testing.T) {
	engine := NewPolicyEngine(nil, nil)
	provenanceCalled := false
	engine.SigVerifier = failingSignatureVerifier{}
	engine.ProvVerifier = verifierFunc{verify: func(string, *Attestation) error {
		provenanceCalled = true
		return nil
	}}

	res := engine.Evaluate(ComputeContentDigest([]byte("artifact")), nil, nil, nil)
	if res.Decision != DecisionDeny {
		t.Fatalf("expected deny, got %s", res.Decision)
	}
	if provenanceCalled {
		t.Fatal("provenance verifier must not run after integrity failure")
	}
}

type failingSignatureVerifier struct{}

func (failingSignatureVerifier) VerifySignature(string, *SignatureVerification) error {
	return errors.New("signature unavailable")
}
