package automation

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/google/go-github/v68/github"
)

func TestGitHubClientIntegrationWithMockServer(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("/repos/testorg/testrepo", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("X-RateLimit-Limit", "5000")
		w.Header().Set("X-RateLimit-Remaining", "4988")
		w.Header().Set("X-RateLimit-Reset", "1700000000")

		repo := &github.Repository{
			ID:          github.Ptr(int64(123456)),
			Name:        github.Ptr("testrepo"),
			FullName:    github.Ptr("testorg/testrepo"),
			Description: github.Ptr("Automated test repository"),
			Private:     github.Ptr(false),
		}
		_ = json.NewEncoder(w).Encode(repo)
	})

	mux.HandleFunc("/repos/testorg/notfound", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusNotFound)
		w.Write([]byte(`{"message": "Not Found", "documentation_url": "https://docs.github.com/rest"}`))
	})

	server := httptest.NewServer(mux)
	defer server.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	client, err := NewGitHubClient(server.Client(), server.URL)
	if err != nil {
		t.Fatalf("failed to create github client: %v", err)
	}

	// 1. Successful repository lookup with rate limit metadata extraction
	repo, rate, err := client.GetRepository(ctx, "testorg", "testrepo")
	if err != nil {
		t.Fatalf("GetRepository failed: %v", err)
	}

	if repo.GetName() != "testrepo" || repo.GetFullName() != "testorg/testrepo" {
		t.Errorf("unexpected repository metadata: %+v", repo)
	}

	if rate == nil || rate.Limit != 5000 || rate.Remaining != 4988 {
		t.Errorf("rate limit metadata was not parsed correctly: %+v", rate)
	}

	// 2. Error handling for 404
	_, _, err = client.GetRepository(ctx, "testorg", "notfound")
	if err == nil {
		t.Fatalf("expected 404 error for nonexistent repository, got nil")
	}
}
