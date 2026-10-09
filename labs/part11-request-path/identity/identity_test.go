package identity

import (
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"errors"
	"io"
	"log"
	"math/big"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"sync/atomic"
	"testing"
	"time"
)

type authority struct {
	cert *x509.Certificate
	key  *ecdsa.PrivateKey
}

func serial(t *testing.T) *big.Int {
	t.Helper()
	n, err := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 128))
	if err != nil {
		t.Fatal(err)
	}
	return n.Add(n, big.NewInt(1))
}
func newCA(t *testing.T) authority {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now()
	tmpl := &x509.Certificate{SerialNumber: serial(t), Subject: pkix.Name{CommonName: "local-lab-CA"}, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign | x509.KeyUsageCRLSign}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &key.PublicKey, key)
	if err != nil {
		t.Fatal(err)
	}
	cert, err := x509.ParseCertificate(der)
	if err != nil {
		t.Fatal(err)
	}
	return authority{cert, key}
}
func leaf(t *testing.T, ca authority, principal string, server bool, expired bool) tls.Certificate {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now()
	tmpl := &x509.Certificate{SerialNumber: serial(t), Subject: pkix.Name{CommonName: "not-an-authority-for-roles"}, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour), KeyUsage: x509.KeyUsageDigitalSignature, ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth}}
	if server {
		tmpl.DNSNames = []string{"service.test"}
		tmpl.ExtKeyUsage = []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}
	}
	if principal != "" {
		u, err := url.Parse(principal)
		if err != nil {
			t.Fatal(err)
		}
		tmpl.URIs = []*url.URL{u}
	}
	if expired {
		tmpl.NotBefore = now.Add(-2 * time.Hour)
		tmpl.NotAfter = now.Add(-time.Hour)
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, ca.cert, &key.PublicKey, ca.key)
	if err != nil {
		t.Fatal(err)
	}
	keyDER, err := x509.MarshalPKCS8PrivateKey(key)
	if err != nil {
		t.Fatal(err)
	}
	c, err := tls.X509KeyPair(pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der}), pem.EncodeToMemory(&pem.Block{Type: "PRIVATE KEY", Bytes: keyDER}))
	if err != nil {
		t.Fatal(err)
	}
	return c
}
func roots(ca authority) *x509.CertPool { p := x509.NewCertPool(); p.AddCert(ca.cert); return p }

func server(t *testing.T, ca authority, authorize func(*http.Request) bool) (*httptest.Server, *atomic.Int32) {
	t.Helper()
	effects := new(atomic.Int32)
	s := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !authorize(r) {
			http.Error(w, "denied", 403)
			return
		}
		if r.Method == http.MethodPost {
			effects.Add(1)
		}
		io.WriteString(w, "allowed")
	}))
	s.Config.ErrorLog = log.New(io.Discard, "", 0)
	s.TLS = &tls.Config{MinVersion: tls.VersionTLS13, Certificates: []tls.Certificate{leaf(t, ca, "", true, false)}, ClientCAs: roots(ca), ClientAuth: tls.RequireAndVerifyClientCert}
	s.StartTLS()
	t.Cleanup(s.Close)
	return s, effects
}

func request(t *testing.T, s *httptest.Server, trust authority, name string, cert *tls.Certificate, method, path string) (int, error) {
	t.Helper()
	config := &tls.Config{MinVersion: tls.VersionTLS13, RootCAs: roots(trust), ServerName: name}
	if cert != nil {
		config.Certificates = []tls.Certificate{*cert}
	}
	transport := &http.Transport{TLSClientConfig: config, Proxy: nil}
	defer transport.CloseIdleConnections()
	client := &http.Client{Transport: transport, Timeout: 3 * time.Second}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, method, s.URL+path, nil)
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("X-Role", "admin") // An untrusted header cannot upgrade a reader.
	resp, err := client.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	_, err = io.Copy(io.Discard, resp.Body)
	return resp.StatusCode, err
}

func TestCertificateBoundaries(t *testing.T) {
	ca, rogue := newCA(t), newCA(t)
	s, effects := server(t, ca, Authorize)
	reader := leaf(t, ca, "urn:go-book:reader", false, false)
	bad := leaf(t, rogue, "urn:go-book:operator", false, false)
	expired := leaf(t, ca, "urn:go-book:operator", false, true)
	wrongEKU := leaf(t, ca, "urn:go-book:operator", true, false)
	for _, tc := range []struct {
		name, hostname string
		trust          authority
		cert           *tls.Certificate
	}{
		{"untrusted_server_CA", "service.test", rogue, &reader},
		{"wrong_SAN", "wrong.test", ca, &reader},
		{"missing_client_cert", "service.test", ca, nil},
		{"untrusted_client_CA", "service.test", ca, &bad},
		{"expired_client", "service.test", ca, &expired},
		{"wrong_client_EKU", "service.test", ca, &wrongEKU},
	} {
		t.Run(tc.name, func(t *testing.T) {
			code, err := request(t, s, tc.trust, tc.hostname, tc.cert, http.MethodPost, "/write")
			if err == nil || code != 0 {
				t.Fatalf("fail-closed got code=%d err=%v", code, err)
			}
			if tc.name == "untrusted_server_CA" {
				var unknown x509.UnknownAuthorityError
				if !errors.As(err, &unknown) {
					t.Fatalf("wrong failure: %v", err)
				}
			}
			if tc.name == "wrong_SAN" {
				var hostname x509.HostnameError
				if !errors.As(err, &hostname) {
					t.Fatalf("wrong failure: %v", err)
				}
			}
			t.Logf("REAL_LOCAL_VERIFIED denied handshake: %v", err)
		})
	}
	if effects.Load() != 0 {
		t.Fatal("rejected handshake mutated state")
	}
	code, err := request(t, s, ca, "service.test", &reader, http.MethodGet, "/read")
	if err != nil || code != 200 {
		t.Fatalf("trusted reader=%d %v", code, err)
	}
	operator := leaf(t, ca, "urn:go-book:operator", false, false)
	code, err = request(t, s, ca, "service.test", &operator, http.MethodPost, "/write")
	if err != nil || code != 200 || effects.Load() != 1 {
		t.Fatalf("operator=%d %v effects=%d", code, err, effects.Load())
	}
}

func TestAuthorizationContract(t *testing.T) {
	ca := newCA(t)
	authorize := Authorize
	if os.Getenv("RELIABILITY_MUTANT") == "trust_equals_role" {
		// Deliberately broken: a trusted certificate grants every action.
		authorize = func(r *http.Request) bool { return r.TLS != nil && len(r.TLS.VerifiedChains) > 0 }
	}
	s, effects := server(t, ca, authorize)
	for _, name := range []string{"urn:go-book:reader", "urn:go-book:unknown", ""} {
		c := leaf(t, ca, name, false, false)
		code, err := request(t, s, ca, "service.test", &c, http.MethodPost, "/write")
		if err != nil || code != 403 || effects.Load() != 0 {
			t.Fatalf("authenticated caller %q unauthorized: status=%d err=%v effects=%d", name, code, err, effects.Load())
		}
	}
	t.Log("valid mTLS handshake does not authorize /write; X-Role ignored")
}

func TestPolicyFailClosedWithoutVerifiedChain(t *testing.T) {
	r := httptest.NewRequest(http.MethodPost, "/write", nil)
	if Authorize(r) {
		t.Fatal("plaintext authorized")
	}
	r.TLS = &tls.ConnectionState{PeerCertificates: []*x509.Certificate{{}}}
	if Authorize(r) {
		t.Fatal("unverified peer authorized")
	}
	r.TLS.VerifiedChains = [][]*x509.Certificate{{}}
	if Authorize(r) {
		t.Fatal("empty chain authorized")
	}
	if Authorize(nil) {
		t.Fatal("nil request authorized")
	}
}
