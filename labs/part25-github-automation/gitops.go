package automation

import (
	"fmt"
	"io"
	"time"

	"github.com/go-git/go-billy/v5"
	"github.com/go-git/go-billy/v5/memfs"
	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing/object"
	"github.com/go-git/go-git/v5/storage/memory"
)

// InMemGitRepository provides safe, in-memory Git operations without filesystem side-effects.
type InMemGitRepository struct {
	repo *git.Repository
	fs   billy.Filesystem
}

// NewInMemGitRepository initializes a new Git repository in memory.
func NewInMemGitRepository() (*InMemGitRepository, error) {
	fs := memfs.New()
	storer := memory.NewStorage()

	repo, err := git.Init(storer, fs)
	if err != nil {
		return nil, fmt.Errorf("failed to init in-memory git repo: %w", err)
	}

	return &InMemGitRepository{
		repo: repo,
		fs:   fs,
	}, nil
}

// WriteFileAndCommit creates or updates a file in the worktree and records a commit.
func (r *InMemGitRepository) WriteFileAndCommit(filePath string, content []byte, author, message string) (string, error) {
	wt, err := r.repo.Worktree()
	if err != nil {
		return "", fmt.Errorf("failed to get worktree: %w", err)
	}

	f, err := r.fs.Create(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to create file %s in memfs: %w", filePath, err)
	}
	n, err := f.Write(content)
	if err == nil && n != len(content) {
		err = io.ErrShortWrite
	}
	if err != nil {
		_ = f.Close()
		return "", fmt.Errorf("failed writing to memfs: %w", err)
	}
	if err := f.Close(); err != nil {
		return "", fmt.Errorf("failed closing memfs file: %w", err)
	}

	if _, err := wt.Add(filePath); err != nil {
		return "", fmt.Errorf("git add %s failed: %w", filePath, err)
	}

	commitHash, err := wt.Commit(message, &git.CommitOptions{
		Author: &object.Signature{
			Name:  author,
			Email: author + "@automated-pipeline.local",
			When:  time.Now(),
		},
	})
	if err != nil {
		return "", fmt.Errorf("git commit failed: %w", err)
	}

	return commitHash.String(), nil
}

// GetHeadCommitHash resolves and returns the current HEAD commit hash.
func (r *InMemGitRepository) GetHeadCommitHash() (string, error) {
	head, err := r.repo.Head()
	if err != nil {
		return "", fmt.Errorf("repository HEAD is unavailable: %w", err)
	}
	return head.Hash().String(), nil
}
