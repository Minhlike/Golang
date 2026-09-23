package store

import (
	"context"
	"testing"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/probe"
)

func newTestStore(t *testing.T) *SQLiteStore {
	t.Helper()
	// Sử dụng in-memory SQLite cho test cô lập
	s, err := NewSQLiteStore(":memory:")
	if err != nil {
		t.Fatalf("new sqlite store: %v", err)
	}

	if err := s.Init(context.Background()); err != nil {
		t.Fatalf("init store: %v", err)
	}

	t.Cleanup(func() {
		_ = s.Close()
	})

	return s
}

func TestStore_RecordAndGetRun(t *testing.T) {
	s := newTestStore(t)
	ctx := context.Background()

	now := time.Now().Truncate(time.Second)
	run := RunRecord{
		ID:           "run-101",
		CreatedAt:    now,
		TargetCount:  2,
		SuccessCount: 1,
		FailureCount: 1,
		Status:       "completed",
	}

	results := []probe.Result{
		{
			TargetID:   "srv-1",
			URL:        "https://example.com/api",
			StatusCode: 200,
			Duration:   45 * time.Millisecond,
			Outcome:    probe.OutcomeSuccess,
			Timestamp:  now,
		},
		{
			TargetID:   "srv-2",
			URL:        "https://example.com/health",
			StatusCode: 500,
			Duration:   120 * time.Millisecond,
			Outcome:    probe.OutcomeFailure,
			Error:      "status 500",
			Timestamp:  now.Add(10 * time.Millisecond),
		},
	}

	if err := s.RecordRun(ctx, run, results); err != nil {
		t.Fatalf("RecordRun failed: %v", err)
	}

	gotRun, gotResults, err := s.GetRun(ctx, "run-101")
	if err != nil {
		t.Fatalf("GetRun failed: %v", err)
	}

	if gotRun.ID != run.ID {
		t.Errorf("expected ID %s, got %s", run.ID, gotRun.ID)
	}
	if gotRun.TargetCount != 2 || gotRun.SuccessCount != 1 || gotRun.FailureCount != 1 {
		t.Errorf("unexpected counts: %+v", gotRun)
	}
	if len(gotResults) != 2 {
		t.Fatalf("expected 2 results, got %d", len(gotResults))
	}

	if gotResults[0].TargetID != "srv-1" || gotResults[0].Outcome != probe.OutcomeSuccess {
		t.Errorf("unexpected result[0]: %+v", gotResults[0])
	}
	if gotResults[1].TargetID != "srv-2" || gotResults[1].Outcome != probe.OutcomeFailure || gotResults[1].Error != "status 500" {
		t.Errorf("unexpected result[1]: %+v", gotResults[1])
	}
}

func TestStore_TransactionRollbackOnCancellation(t *testing.T) {
	s := newTestStore(t)

	// Tạo context bị hủy trước khi lưu
	ctx, cancel := context.WithCancel(context.Background())
	cancel() // Hủy ngay

	run := RunRecord{
		ID:           "run-rollback",
		CreatedAt:    time.Now(),
		TargetCount:  1,
		SuccessCount: 1,
		FailureCount: 0,
		Status:       "completed",
	}
	results := []probe.Result{
		{
			TargetID:  "t1",
			URL:       "http://example.com",
			Outcome:   probe.OutcomeSuccess,
			Timestamp: time.Now(),
		},
	}

	err := s.RecordRun(ctx, run, results)
	if err == nil {
		t.Fatalf("expected error on cancelled context, got nil")
	}

	// Xác minh nguyên tắc nguyên tử: không có bản ghi nào lọt vào database
	activeCtx := context.Background()
	_, _, err = s.GetRun(activeCtx, "run-rollback")
	if err != ErrNotFound {
		t.Fatalf("expected ErrNotFound because transaction must roll back, got: %v", err)
	}
}

func TestStore_GetRun_NotFound(t *testing.T) {
	s := newTestStore(t)
	_, _, err := s.GetRun(context.Background(), "non-existent")
	if err != ErrNotFound {
		t.Fatalf("expected ErrNotFound, got: %v", err)
	}
}

func TestStore_Ping(t *testing.T) {
	s := newTestStore(t)
	if err := s.Ping(context.Background()); err != nil {
		t.Fatalf("Ping failed: %v", err)
	}
}
