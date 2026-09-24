package supplychain

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"testing"
)

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
