package storage

import (
	"context"

	"github.com/aws/smithy-go/middleware"
	smithyhttp "github.com/aws/smithy-go/transport/http"
)

// AuditHeaderMiddleware is a custom Smithy middleware that injects an audit origin header
// into all outgoing HTTP requests in the SDK pipeline.
type AuditHeaderMiddleware struct {
	Origin string
}

func (m *AuditHeaderMiddleware) ID() string {
	return "AuditHeaderMiddleware"
}

func (m *AuditHeaderMiddleware) HandleBuild(
	ctx context.Context,
	in middleware.BuildInput,
	next middleware.BuildHandler,
) (out middleware.BuildOutput, metadata middleware.Metadata, err error) {
	req, ok := in.Request.(*smithyhttp.Request)
	if ok && req != nil {
		req.Header.Set("X-Audit-Origin", m.Origin)
	}
	return next.HandleBuild(ctx, in)
}
