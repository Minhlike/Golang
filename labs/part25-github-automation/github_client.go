package automation

import (
	"context"
	"fmt"
	"net/http"
	"net/url"
	"strings"

	"github.com/google/go-github/v68/github"
)

// GitHubClient wraps the official google/go-github client with configured base URL and transport.
type GitHubClient struct {
	client *github.Client
}

// NewGitHubClient initializes a typed GitHub client pointing to github.com or a mock httptest endpoint.
func NewGitHubClient(httpClient *http.Client, baseURL string) (*GitHubClient, error) {
	gh := github.NewClient(httpClient)
	if baseURL != "" {
		if !strings.HasSuffix(baseURL, "/") {
			baseURL += "/"
		}
		u, err := url.Parse(baseURL)
		if err != nil {
			return nil, fmt.Errorf("invalid github base url: %w", err)
		}
		gh.BaseURL = u
	}
	return &GitHubClient{client: gh}, nil
}

// GetRepository fetches repository details and extracts API rate limit information.
func (c *GitHubClient) GetRepository(ctx context.Context, owner, repo string) (*github.Repository, *github.Rate, error) {
	repository, resp, err := c.client.Repositories.Get(ctx, owner, repo)
	if err != nil {
		return nil, nil, err
	}
	var rate *github.Rate
	if resp != nil {
		rate = &resp.Rate
	}
	return repository, rate, nil
}
