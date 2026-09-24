package storage

import (
	"context"
	"errors"
	"fmt"
	"io"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
	"github.com/aws/smithy-go"
)

// CloudStorage encapsulates Amazon S3 operations using AWS SDK for Go v2.
type CloudStorage struct {
	client *s3.Client
}

// NewCloudStorage creates a CloudStorage instance with the provided S3 client.
func NewCloudStorage(client *s3.Client) *CloudStorage {
	return &CloudStorage{client: client}
}

// PutObject streams data into an S3 bucket key.
func (s *CloudStorage) PutObject(ctx context.Context, bucket, key string, body io.Reader) error {
	_, err := s.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
		Body:   body,
	})
	if err != nil {
		return fmt.Errorf("PutObject failed for %s/%s: %w", bucket, key, err)
	}
	return nil
}

// GetObject downloads data from an S3 bucket key.
func (s *CloudStorage) GetObject(ctx context.Context, bucket, key string) ([]byte, error) {
	resp, err := s.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(bucket),
		Key:    aws.String(key),
	})
	if err != nil {
		return nil, fmt.Errorf("GetObject failed for %s/%s: %w", bucket, key, err)
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	return data, nil
}

// ListAllKeys iterates over all pages using the official SDK Paginator without buffering all objects at once.
func (s *CloudStorage) ListAllKeys(ctx context.Context, bucket, prefix string) ([]string, error) {
	paginator := s3.NewListObjectsV2Paginator(s.client, &s3.ListObjectsV2Input{
		Bucket: aws.String(bucket),
		Prefix: aws.String(prefix),
	})

	var keys []string
	pageCount := 0

	for paginator.HasMorePages() {
		pageCount++
		page, err := paginator.NextPage(ctx)
		if err != nil {
			return nil, fmt.Errorf("failed fetching page %d: %w", pageCount, err)
		}

		for _, item := range page.Contents {
			if item.Key != nil {
				keys = append(keys, *item.Key)
			}
		}
	}

	return keys, nil
}

// ClassifyError inspects an error from AWS SDK v2 and categorizes it using Smithy type assertions.
func ClassifyError(err error) (isRetryable bool, errorCode string) {
	if err == nil {
		return false, ""
	}

	// 1. Check for specific typed S3 service errors
	var noSuchKey *types.NoSuchKey
	if errors.As(err, &noSuchKey) {
		return false, "NoSuchKey"
	}

	var noSuchBucket *types.NoSuchBucket
	if errors.As(err, &noSuchBucket) {
		return false, "NoSuchBucket"
	}

	// 2. Check for general Smithy APIError
	var apiErr smithy.APIError
	if errors.As(err, &apiErr) {
		code := apiErr.ErrorCode()
		// Common AWS throttling and transient error codes
		switch code {
		case "SlowDown", "ThrottlingException", "TooManyRequestsException", "RequestTimeout", "ServiceUnavailable":
			return true, code
		default:
			return false, code
		}
	}

	return false, "UnknownError"
}
