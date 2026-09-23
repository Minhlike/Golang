package store

import (
	"context"
	"testing"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/probe"
)

func newTestStore(t *testing.T) *SQLiteStore {
	t.Helper()
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

	start := time.Now().Truncate(time.Second).Add(-5 * time.Second)
	complete := start.Add(4 * time.Second)

	run := RunRecord{
		ID:           "run-101",
		StartedAt:    start,
		CompletedAt:  complete,
		TargetCount:  2,
		SuccessCount: 1,
		FailureCount: 1,
		Status:       "completed",
	}

	results := []probe.Result{
		{
			TargetID:       "srv-1",
			URL:            "https://example.com/api",
			StatusCode:     200,
			DurationNs:     45000000,
			DurationMs:     45.0,
			Outcome:        probe.OutcomeSuccess,
			ReusedEligible: true,
			Timestamp:      start.Add(100 * time.Millisecond),
		},
		{
			TargetID:       "srv-2",
			URL:            "https://example.com/health",
			StatusCode:     500,
			DurationNs:     120000000,
			DurationMs:     120.0,
			Outcome:        probe.OutcomeFailure,
			ReusedEligible: false,
			Error:          "status 500",
			Timestamp:      start.Add(200 * time.Millisecond),
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
	if !gotRun.StartedAt.Equal(start) || !gotRun.CompletedAt.Equal(complete) {
		t.Errorf("unexpected timestamps: started=%v, completed=%v", gotRun.StartedAt, gotRun.CompletedAt)
	}
	if gotRun.TargetCount != 2 || gotRun.SuccessCount != 1 || gotRun.FailureCount != 1 {
		t.Errorf("unexpected counts: %+v", gotRun)
	}
	if len(gotResults) != 2 {
		t.Fatalf("expected 2 results, got %d", len(gotResults))
	}

	if gotResults[0].TargetID != "srv-1" || gotResults[0].Outcome != probe.OutcomeSuccess || !gotResults[0].ReusedEligible {
		t.Errorf("unexpected result[0]: %+v", gotResults[0])
	}
	if gotResults[1].TargetID != "srv-2" || gotResults[1].Outcome != probe.OutcomeFailure || gotResults[1].ReusedEligible {
		t.Errorf("unexpected result[1]: %+v", gotResults[1])
	}
}

// TestStore_DeterministicRollbackAfterPartialMutation chứng minh bằng chứng thực nghiệm:
// Sau khi lệnh INSERT INTO runs đã thực thi thành công, một lỗi vi phạm ràng buộc
// (CHECK constraint) xảy ra ở bước INSERT probe_results sẽ kích hoạt rollback hoàn toàn,
// không để lại bản ghi nào trong cả bảng runs lẫn bảng probe_results.
func TestStore_DeterministicRollbackAfterPartialMutation(t *testing.T) {
	s := newTestStore(t)
	ctx := context.Background()

	run := RunRecord{
		ID:           "run-rollback-proof",
		StartedAt:    time.Now().Add(-1 * time.Second),
		CompletedAt:  time.Now(),
		TargetCount:  2,
		SuccessCount: 1,
		FailureCount: 1,
		Status:       "completed",
	}

	// Kết quả thứ nhất hợp lệ, kết quả thứ hai cố ý vi phạm ràng buộc CHECK (status_code >= 0)
	results := []probe.Result{
		{
			TargetID:   "t1",
			URL:        "http://example.com/ok",
			StatusCode: 200,
			DurationNs: 10000000,
			Outcome:    probe.OutcomeSuccess,
			Timestamp:  time.Now(),
		},
		{
			TargetID:   "t2-invalid",
			URL:        "http://example.com/invalid",
			StatusCode: -1, // Vi phạm CONSTRAINT chk_status_code CHECK (status_code >= 0)
			DurationNs: 20000000,
			Outcome:    probe.OutcomeFailure,
			Timestamp:  time.Now(),
		},
	}

	err := s.RecordRun(ctx, run, results)
	if err == nil {
		t.Fatalf("expected constraint violation error, got nil")
	}

	// 1. Kiểm tra qua API GetRun
	_, _, err = s.GetRun(ctx, "run-rollback-proof")
	if err != ErrNotFound {
		t.Fatalf("expected ErrNotFound because transaction must roll back, got: %v", err)
	}

	// 2. Truy vấn trực tiếp mức database để chứng minh không còn tàn dư
	var runCount int
	if queryErr := s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM runs WHERE id = ?", "run-rollback-proof").Scan(&runCount); queryErr != nil {
		t.Fatalf("query runs count: %v", queryErr)
	}
	if runCount != 0 {
		t.Errorf("expected 0 rows in runs after rollback, got %d", runCount)
	}

	var resultsCount int
	if queryErr := s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM probe_results WHERE run_id = ?", "run-rollback-proof").Scan(&resultsCount); queryErr != nil {
		t.Fatalf("query probe_results count: %v", queryErr)
	}
	if resultsCount != 0 {
		t.Errorf("expected 0 rows in probe_results after rollback, got %d", resultsCount)
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
