package supplychain

import (
	"crypto/ecdsa"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"regexp"
	"strings"
)

var digestRegex = regexp.MustCompile(`^sha256:[a-f0-9]{64}$`)

type Decision string

const (
	DecisionAllow Decision = "ALLOW"
	DecisionDeny  Decision = "DENY"
)

// Vulnerability represents a finding with govulncheck symbol reachability semantics.
type Vulnerability struct {
	ID        string `json:"id"`
	Package   string `json:"package"`
	Symbol    string `json:"symbol"`
	Severity  string `json:"severity"` // "CRITICAL", "HIGH", "MEDIUM", "LOW"
	Reachable bool   `json:"reachable"` // True if called in execution call-graph
}

// Attestation represents SLSA provenance metadata.
type Attestation struct {
	BuilderID     string `json:"builderId"`
	SubjectDigest string `json:"subjectDigest"`
}

// SignatureVerification represents cryptographic Cosign signature proof.
type SignatureVerification struct {
	PublicKey *ecdsa.PublicKey
	RBytes    []byte
	SBytes    []byte
	Signature []byte
	Issuer    string
}

// EvaluationResult details the policy decision and rationale.
type EvaluationResult struct {
	Decision   Decision `json:"decision"`
	Violations []string `json:"violations,omitempty"`
	Warnings   []string `json:"warnings,omitempty"`
}

// PolicyEngine enforces fail-closed supply chain integrity gates.
type PolicyEngine struct {
	TrustedBuilders []string
	TrustedIssuers  []string
}

// NewPolicyEngine creates a verification engine with trusted identity anchors.
func NewPolicyEngine(trustedBuilders, trustedIssuers []string) *PolicyEngine {
	return &PolicyEngine{
		TrustedBuilders: trustedBuilders,
		TrustedIssuers:  trustedIssuers,
	}
}

// VerifyDigest validates that the artifact uses an immutable content-addressed OCI digest.
func VerifyDigest(digest string) error {
	if !digestRegex.MatchString(digest) {
		return errors.New("invalid or mutable OCI digest: must be sha256:64hex")
	}
	return nil
}

// VerifySignature validates ECDSA P-256 signature against artifact digest and OIDC issuer.
func (e *PolicyEngine) VerifySignature(digest string, sig *SignatureVerification) error {
	if sig == nil || sig.PublicKey == nil {
		return errors.New("missing cryptographic signature or public key")
	}

	// 1. Verify trusted OIDC identity issuer
	trustedIssuer := false
	for _, ti := range e.TrustedIssuers {
		if sig.Issuer == ti {
			trustedIssuer = true
			break
		}
	}
	if !trustedIssuer {
		return fmt.Errorf("untrusted OIDC signature issuer: %s", sig.Issuer)
	}

	// 2. Cryptographic signature check
	hash := sha256.Sum256([]byte(digest))
	if len(sig.Signature) == 0 {
		return errors.New("empty signature payload")
	}

	valid := ecdsa.VerifyASN1(sig.PublicKey, hash[:], sig.Signature)
	if !valid {
		return errors.New("signature verification failed: cryptographic signature mismatch")
	}

	return nil
}

// Evaluate evaluates all supply chain invariants following the fail-closed principle.
func (e *PolicyEngine) Evaluate(
	artifactDigest string,
	sig *SignatureVerification,
	att *Attestation,
	vulns []Vulnerability,
) EvaluationResult {
	res := EvaluationResult{Decision: DecisionAllow}

	// 1. Digest immutability gate
	if err := VerifyDigest(artifactDigest); err != nil {
		res.Decision = DecisionDeny
		res.Violations = append(res.Violations, err.Error())
		return res // Fail closed immediately
	}

	// 2. Cosign signature verification gate
	if err := e.VerifySignature(artifactDigest, sig); err != nil {
		res.Decision = DecisionDeny
		res.Violations = append(res.Violations, err.Error())
	}

	// 3. SLSA Provenance and Builder identity gate
	if att == nil {
		res.Decision = DecisionDeny
		res.Violations = append(res.Violations, "missing SLSA provenance attestation")
	} else {
		if att.SubjectDigest != artifactDigest {
			res.Decision = DecisionDeny
			res.Violations = append(res.Violations, "provenance subject digest does not match artifact digest")
		}

		builderTrusted := false
		for _, tb := range e.TrustedBuilders {
			if att.BuilderID == tb {
				builderTrusted = true
				break
			}
		}
		if !builderTrusted {
			res.Decision = DecisionDeny
			res.Violations = append(res.Violations, fmt.Sprintf("untrusted builder identity: %s", att.BuilderID))
		}
	}

	// 4. Vulnerability gate with govulncheck reachability semantics
	for _, v := range vulns {
		isHighOrCritical := strings.EqualFold(v.Severity, "CRITICAL") || strings.EqualFold(v.Severity, "HIGH")

		if isHighOrCritical {
			if v.Reachable {
				// Symbol is called in application binary: REJECT
				res.Decision = DecisionDeny
				res.Violations = append(res.Violations,
					fmt.Sprintf("reachable %s vulnerability %s in %s (symbol: %s)",
						v.Severity, v.ID, v.Package, v.Symbol))
			} else {
				// Vulnerability exists in module dependency graph but symbol is NOT called: WARN
				res.Warnings = append(res.Warnings,
					fmt.Sprintf("uncalled %s vulnerability %s in %s: tolerated under policy",
						v.Severity, v.ID, v.Package))
			}
		}
	}

	return res
}

// ComputeContentDigest calculates standard sha256:<hex> for arbitrary payload.
func ComputeContentDigest(payload []byte) string {
	h := sha256.Sum256(payload)
	return "sha256:" + hex.EncodeToString(h[:])
}
