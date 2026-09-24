package storage

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/smithy-go"
	"github.com/aws/smithy-go/middleware"
)

// TestTemporaryCredentialRefresh verifies automatic rotation of short-lived credentials.
func TestTemporaryCredentialRefresh(t *testing.T) {
	provider := NewDynamicCredentialProvider("arn:aws:iam::123456789012:role/AppRole", 50*time.Millisecond)

	ctx := context.Background()
	cred1, err := provider.Retrieve(ctx)
	if err != nil {
		t.Fatalf("first retrieve failed: %v", err)
	}
	if provider.RetrieveCount() != 1 {
		t.Fatalf("expected 1 retrieve, got %d", provider.RetrieveCount())
	}
	if !cred1.CanExpire {
		t.Errorf("expected CanExpire=true")
	}

	// Wait for credentials to expire
	time.Sleep(60 * time.Millisecond)

	if time.Now().Before(cred1.Expires) {
		t.Fatalf("expected credentials to be expired")
	}

	// Retrieve refreshed credentials
	cred2, err := provider.Retrieve(ctx)
	if err != nil {
		t.Fatalf("second retrieve failed: %v", err)
	}
	if provider.RetrieveCount() != 2 {
		t.Fatalf("expected 2 retrieves, got %d", provider.RetrieveCount())
	}
	if cred1.AccessKeyID == cred2.AccessKeyID {
		t.Errorf("expected refreshed access key, got identical: %s", cred1.AccessKeyID)
	}
}

// TestCustomSmithyMiddlewareAuditHeader proves that Smithy middleware injects headers into outgoing HTTP calls.
func TestCustomSmithyMiddlewareAuditHeader(t *testing.T) {
	var capturedAuditHeader atomic.Value

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedAuditHeader.Store(r.Header.Get("X-Audit-Origin"))
		w.Header().Set("Content-Type", "application/xml")
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	cfg := aws.Config{
		Region: "us-east-1",
		Credentials: credentials.NewStaticCredentialsProvider(
			"AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "",
		),
	}

	s3Client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		o.BaseEndpoint = aws.String(server.URL)
		o.UsePathStyle = true
		o.APIOptions = append(o.APIOptions, func(stack *middleware.Stack) error {
			return stack.Build.Add(&AuditHeaderMiddleware{Origin: "automated-backup-worker"}, middleware.After)
		})
	})

	storage := NewCloudStorage(s3Client)
	err := storage.PutObject(context.Background(), "my-bucket", "config.json", bytes.NewReader([]byte("{}")))
	if err != nil {
		t.Fatalf("PutObject failed: %v", err)
	}

	val, ok := capturedAuditHeader.Load().(string)
	if !ok || val != "automated-backup-worker" {
		t.Fatalf("expected X-Audit-Origin='automated-backup-worker', got %q", val)
	}
}

// TestS3OperationsPutAndGet verifies PutObject and GetObject stream handling.
func TestS3OperationsPutAndGet(t *testing.T) {
	payload := []byte("production-cluster-backup-payload-v2")

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodPut:
			w.WriteHeader(http.StatusOK)
		case http.MethodGet:
			w.Header().Set("Content-Type", "application/octet-stream")
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write(payload)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	}))
	defer server.Close()

	cfg := aws.Config{
		Region: "us-east-1",
		Credentials: credentials.NewStaticCredentialsProvider(
			"AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "",
		),
	}

	s3Client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		o.BaseEndpoint = aws.String(server.URL)
		o.UsePathStyle = true
	})

	storage := NewCloudStorage(s3Client)

	// Test Put
	err := storage.PutObject(context.Background(), "logs-bucket", "2026/09/audit.log", bytes.NewReader(payload))
	if err != nil {
		t.Fatalf("PutObject failed: %v", err)
	}

	// Test Get
	data, err := storage.GetObject(context.Background(), "logs-bucket", "2026/09/audit.log")
	if err != nil {
		t.Fatalf("GetObject failed: %v", err)
	}
	if !bytes.Equal(data, payload) {
		t.Fatalf("expected %q, got %q", string(payload), string(data))
	}
}

// TestPaginatorListAllKeys proves that ListObjectsV2Paginator handles multiple pages seamlessly.
func TestPaginatorListAllKeys(t *testing.T) {
	requestCount := atomic.Int64{}

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		reqNum := requestCount.Add(1)
		w.Header().Set("Content-Type", "application/xml")
		w.WriteHeader(http.StatusOK)

		if reqNum == 1 {
			// Page 1 with continuation token
			xmlResp := `<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>my-bucket</Name>
    <IsTruncated>true</IsTruncated>
    <NextContinuationToken>token-page-2</NextContinuationToken>
    <Contents><Key>file-1.txt</Key></Contents>
    <Contents><Key>file-2.txt</Key></Contents>
</ListBucketResult>`
			_, _ = fmt.Fprint(w, xmlResp)
		} else {
			// Page 2 (final)
			xmlResp := `<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Name>my-bucket</Name>
    <IsTruncated>false</IsTruncated>
    <Contents><Key>file-3.txt</Key></Contents>
</ListBucketResult>`
			_, _ = fmt.Fprint(w, xmlResp)
		}
	}))
	defer server.Close()

	cfg := aws.Config{
		Region: "us-east-1",
		Credentials: credentials.NewStaticCredentialsProvider(
			"AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "",
		),
	}

	s3Client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		o.BaseEndpoint = aws.String(server.URL)
		o.UsePathStyle = true
	})

	storage := NewCloudStorage(s3Client)
	keys, err := storage.ListAllKeys(context.Background(), "my-bucket", "")
	if err != nil {
		t.Fatalf("ListAllKeys failed: %v", err)
	}

	if len(keys) != 3 {
		t.Fatalf("expected 3 keys, got %d: %v", len(keys), keys)
	}
	expectedKeys := []string{"file-1.txt", "file-2.txt", "file-3.txt"}
	for i, k := range keys {
		if k != expectedKeys[i] {
			t.Errorf("at index %d: expected %s, got %s", i, expectedKeys[i], k)
		}
	}
}

// TestErrorClassification verifies typed error classification using Smithy APIError.
func TestErrorClassification(t *testing.T) {
	retryableErr := &smithy.GenericAPIError{
		Code:    "SlowDown",
		Message: "Please reduce your request rate.",
	}
	isRetryable, code := ClassifyError(retryableErr)
	if !isRetryable || code != "SlowDown" {
		t.Errorf("expected SlowDown to be retryable, got isRetryable=%v, code=%s", isRetryable, code)
	}

	nonRetryableErr := &smithy.GenericAPIError{
		Code:    "AccessDenied",
		Message: "User is not authorized to perform: s3:GetObject",
	}
	isRetryable, code = ClassifyError(nonRetryableErr)
	if isRetryable || code != "AccessDenied" {
		t.Errorf("expected AccessDenied to be non-retryable, got isRetryable=%v, code=%s", isRetryable, code)
	}
}
