package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"

	"example.com/golang-master/projects/opsprobe/internal/probe"
	_ "modernc.org/sqlite"
)

// ErrNotFound được trả về khi không tìm thấy bản ghi yêu cầu.
var ErrNotFound = errors.New("record not found")

// RunRecord đại diện cho metadata tổng hợp của một đợt probe với mốc thời gian chính xác.
type RunRecord struct {
	ID           string    `json:"id"`
	StartedAt    time.Time `json:"started_at"`
	CompletedAt  time.Time `json:"completed_at"`
	TargetCount  int       `json:"target_count"`
	SuccessCount int       `json:"success_count"`
	FailureCount int       `json:"failure_count"`
	Status       string    `json:"status"` // "completed", "failed", "canceled"
}

// Store định nghĩa contract lưu trữ cho opsprobe.
type Store interface {
	Init(ctx context.Context) error
	RecordRun(ctx context.Context, run RunRecord, results []probe.Result) error
	GetRun(ctx context.Context, runID string) (*RunRecord, []probe.Result, error)
	ListRuns(ctx context.Context, limit int) ([]RunRecord, error)
	Ping(ctx context.Context) error
	Close() error
}

// SQLiteStore cài đặt Store trên nền tảng database/sql và SQLite.
type SQLiteStore struct {
	db *sql.DB
}

// NewSQLiteStore khởi tạo kết nối SQLite với cấu hình connection pool an toàn.
func NewSQLiteStore(dsn string) (*SQLiteStore, error) {
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("open sqlite: %w", err)
	}

	// SQLite cần giới hạn 1 open connection khi chạy in-memory hoặc đơn luồng ghi
	// để tránh lỗi SQLITE_BUSY hoặc database table locked do race giữa các transaction.
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	db.SetConnMaxLifetime(0)

	return &SQLiteStore{db: db}, nil
}

// Init tạo các bảng schema cần thiết với ràng buộc toàn vẹn khóa ngoại và check constraints.
func (s *SQLiteStore) Init(ctx context.Context) error {
	// Bật foreign key enforcement trong SQLite
	if _, err := s.db.ExecContext(ctx, "PRAGMA foreign_keys = ON;"); err != nil {
		return fmt.Errorf("enable foreign_keys: %w", err)
	}

	schema := `
	CREATE TABLE IF NOT EXISTS runs (
		id TEXT PRIMARY KEY,
		started_at TIMESTAMP NOT NULL,
		completed_at TIMESTAMP NOT NULL,
		target_count INTEGER NOT NULL,
		success_count INTEGER NOT NULL,
		failure_count INTEGER NOT NULL,
		status TEXT NOT NULL CHECK(status IN ('completed', 'failed', 'canceled'))
	);

	CREATE TABLE IF NOT EXISTS probe_results (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		run_id TEXT NOT NULL,
		target_id TEXT NOT NULL,
		url TEXT NOT NULL,
		status_code INTEGER NOT NULL,
		duration_ns INTEGER NOT NULL,
		outcome TEXT NOT NULL CHECK(outcome IN ('success', 'failure', 'timeout', 'cancel')),
		reused_eligible INTEGER NOT NULL DEFAULT 0,
		error_msg TEXT,
		timestamp TIMESTAMP NOT NULL,
		FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE,
		CONSTRAINT chk_status_code CHECK (status_code >= 0)
	);

	CREATE INDEX IF NOT EXISTS idx_probe_results_run_id ON probe_results(run_id);
	`

	if _, err := s.db.ExecContext(ctx, schema); err != nil {
		return fmt.Errorf("init schema: %w", err)
	}

	return nil
}

// RecordRun lưu metadata đợt chạy và toàn bộ kết quả probe trong MỘT TRANSACTION NGUYÊN TỬ.
// Nếu bất kỳ thao tác nào lỗi, toàn bộ transaction sẽ rollback để bảo đảm tính nhất quán.
func (s *SQLiteStore) RecordRun(ctx context.Context, run RunRecord, results []probe.Result) error {
	if run.ID == "" {
		return errors.New("run id must not be empty")
	}

	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("begin transaction: %w", err)
	}
	defer tx.Rollback() // An toàn: không có tác dụng nếu tx.Commit() đã thành công

	// 1. Chèn bản ghi đợt chạy
	const insertRunQuery = `
	INSERT INTO runs (id, started_at, completed_at, target_count, success_count, failure_count, status)
	VALUES (?, ?, ?, ?, ?, ?, ?);
	`
	_, err = tx.ExecContext(ctx, insertRunQuery,
		run.ID,
		run.StartedAt.UTC(),
		run.CompletedAt.UTC(),
		run.TargetCount,
		run.SuccessCount,
		run.FailureCount,
		run.Status,
	)
	if err != nil {
		return fmt.Errorf("insert run: %w", err)
	}

	// 2. Chèn từng kết quả probe bằng prepared statement
	if len(results) > 0 {
		const insertResultQuery = `
		INSERT INTO probe_results (run_id, target_id, url, status_code, duration_ns, outcome, reused_eligible, error_msg, timestamp)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
		`
		stmt, err := tx.PrepareContext(ctx, insertResultQuery)
		if err != nil {
			return fmt.Errorf("prepare insert result: %w", err)
		}
		defer stmt.Close()

		for _, r := range results {
			reusedInt := 0
			if r.ReusedEligible {
				reusedInt = 1
			}

			_, err = stmt.ExecContext(ctx,
				run.ID,
				r.TargetID,
				r.URL,
				r.StatusCode,
				r.DurationNs,
				string(r.Outcome),
				reusedInt,
				r.Error,
				r.Timestamp.UTC(),
			)
			if err != nil {
				return fmt.Errorf("insert probe result (target: %s): %w", r.TargetID, err)
			}
		}
	}

	// 3. Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit transaction: %w", err)
	}

	return nil
}

// GetRun truy vấn bản ghi run và toàn bộ danh sách kết quả probe tương ứng.
func (s *SQLiteStore) GetRun(ctx context.Context, runID string) (*RunRecord, []probe.Result, error) {
	const selectRun = `
	SELECT id, started_at, completed_at, target_count, success_count, failure_count, status
	FROM runs
	WHERE id = ?;
	`
	row := s.db.QueryRowContext(ctx, selectRun, runID)
	var run RunRecord
	var startedAt, completedAt time.Time
	if err := row.Scan(&run.ID, &startedAt, &completedAt, &run.TargetCount, &run.SuccessCount, &run.FailureCount, &run.Status); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, nil, ErrNotFound
		}
		return nil, nil, fmt.Errorf("query run: %w", err)
	}
	run.StartedAt = startedAt
	run.CompletedAt = completedAt

	const selectResults = `
	SELECT target_id, url, status_code, duration_ns, outcome, reused_eligible, error_msg, timestamp
	FROM probe_results
	WHERE run_id = ?
	ORDER BY id ASC;
	`
	rows, err := s.db.QueryContext(ctx, selectResults, runID)
	if err != nil {
		return nil, nil, fmt.Errorf("query probe results: %w", err)
	}
	defer rows.Close()

	var results []probe.Result
	for rows.Next() {
		var r probe.Result
		var outcomeStr string
		var durationNS int64
		var reusedInt int
		var ts time.Time
		var errorMsg sql.NullString

		if err := rows.Scan(&r.TargetID, &r.URL, &r.StatusCode, &durationNS, &outcomeStr, &reusedInt, &errorMsg, &ts); err != nil {
			return nil, nil, fmt.Errorf("scan probe result: %w", err)
		}

		r.DurationNs = durationNS
		r.DurationMs = float64(durationNS) / 1e6
		r.Outcome = probe.Outcome(outcomeStr)
		r.ReusedEligible = (reusedInt == 1)
		r.Timestamp = ts
		if errorMsg.Valid {
			r.Error = errorMsg.String
		}

		results = append(results, r)
	}

	if err := rows.Err(); err != nil {
		return nil, nil, fmt.Errorf("iterate probe results: %w", err)
	}

	return &run, results, nil
}

// ListRuns liệt kê các đợt chạy gần nhất.
func (s *SQLiteStore) ListRuns(ctx context.Context, limit int) ([]RunRecord, error) {
	if limit <= 0 {
		limit = 10
	}
	const query = `
	SELECT id, started_at, completed_at, target_count, success_count, failure_count, status
	FROM runs
	ORDER BY started_at DESC
	LIMIT ?;
	`
	rows, err := s.db.QueryContext(ctx, query, limit)
	if err != nil {
		return nil, fmt.Errorf("list runs: %w", err)
	}
	defer rows.Close()

	var runs []RunRecord
	for rows.Next() {
		var r RunRecord
		var startedAt, completedAt time.Time
		if err := rows.Scan(&r.ID, &startedAt, &completedAt, &r.TargetCount, &r.SuccessCount, &r.FailureCount, &r.Status); err != nil {
			return nil, fmt.Errorf("scan run item: %w", err)
		}
		r.StartedAt = startedAt
		r.CompletedAt = completedAt
		runs = append(runs, r)
	}

	return runs, rows.Err()
}

// Ping kiểm tra khả năng truy cập database.
func (s *SQLiteStore) Ping(ctx context.Context) error {
	return s.db.PingContext(ctx)
}

// Close đóng database pool an toàn.
func (s *SQLiteStore) Close() error {
	return s.db.Close()
}
