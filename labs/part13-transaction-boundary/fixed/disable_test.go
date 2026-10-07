package fixed

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"testing"

	_ "modernc.org/sqlite"
)

func TestDisableCommitsCheckAndAuditEvent(t *testing.T) {
	db := openTestDB(t, "CREATE TABLE check_events (check_id INTEGER NOT NULL, action TEXT NOT NULL CHECK (action = 'disabled'))")
	insertCheck(t, db, 42, true)

	if err := Disable(context.Background(), db, 42); err != nil {
		t.Fatalf("Disable() error = %v", err)
	}
	if enabled := checkEnabled(t, db, 42); enabled {
		t.Fatal("check remained enabled after a successful disable")
	}
	if got := eventCount(t, db, 42); got != 1 {
		t.Fatalf("event count = %d, want 1", got)
	}
}

func TestDisableRollsBackWhenAuditCannotBeWritten(t *testing.T) {
	db := openTestDB(t, "CREATE TABLE check_events (check_id INTEGER NOT NULL, action TEXT NOT NULL CHECK (action = 'created'))")
	insertCheck(t, db, 42, true)

	if err := Disable(context.Background(), db, 42); err == nil {
		t.Fatal("Disable() error = nil, want audit constraint error")
	}
	if enabled := checkEnabled(t, db, 42); !enabled {
		t.Fatal("check was disabled even though its audit event failed")
	}
}

func TestDisableDoesNotInventAnAuditEvent(t *testing.T) {
	db := openTestDB(t, "CREATE TABLE check_events (check_id INTEGER NOT NULL, action TEXT NOT NULL CHECK (action = 'disabled'))")

	err := Disable(context.Background(), db, 404)
	if !errors.Is(err, ErrCheckNotFound) {
		t.Fatalf("Disable() error = %v, want ErrCheckNotFound", err)
	}
	if got := eventCount(t, db, 404); got != 0 {
		t.Fatalf("event count = %d, want 0", got)
	}
}

func TestDisableRejectsNilDatabase(t *testing.T) {
	if err := Disable(context.Background(), nil, 42); err == nil {
		t.Fatal("Disable() accepted a nil database")
	}
}

func TestDisableRepeatedCallRecordsAnotherAuditEvent(t *testing.T) {
	db := openTestDB(t, "CREATE TABLE check_events (check_id INTEGER NOT NULL, action TEXT NOT NULL CHECK (action = 'disabled'))")
	insertCheck(t, db, 42, true)

	if err := Disable(context.Background(), db, 42); err != nil {
		t.Fatalf("first Disable() error = %v", err)
	}
	if err := Disable(context.Background(), db, 42); err != nil {
		t.Fatalf("second Disable() error = %v", err)
	}
	if got := eventCount(t, db, 42); got != 2 {
		t.Fatalf("event count after two calls = %d, want 2", got)
	}
}

func openTestDB(t *testing.T, auditSchema string) *sql.DB {
	t.Helper()
	dsn := fmt.Sprintf("file:%s?mode=memory&cache=shared", strings.ReplaceAll(t.Name(), "/", "_"))
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		t.Fatalf("open sqlite: %v", err)
	}
	db.SetMaxOpenConns(1)
	t.Cleanup(func() { db.Close() })
	for _, statement := range []string{
		"CREATE TABLE checks (id INTEGER PRIMARY KEY, enabled INTEGER NOT NULL)",
		auditSchema,
	} {
		if _, err := db.Exec(statement); err != nil {
			t.Fatalf("create schema: %v", err)
		}
	}
	return db
}

func insertCheck(t *testing.T, db *sql.DB, id int64, enabled bool) {
	t.Helper()
	if _, err := db.Exec("INSERT INTO checks(id, enabled) VALUES (?, ?)", id, enabled); err != nil {
		t.Fatalf("insert check: %v", err)
	}
}

func checkEnabled(t *testing.T, db *sql.DB, id int64) bool {
	t.Helper()
	var enabled bool
	if err := db.QueryRow("SELECT enabled FROM checks WHERE id = ?", id).Scan(&enabled); err != nil {
		t.Fatalf("read check: %v", err)
	}
	return enabled
}

func eventCount(t *testing.T, db *sql.DB, id int64) int {
	t.Helper()
	var count int
	if err := db.QueryRow("SELECT COUNT(*) FROM check_events WHERE check_id = ?", id).Scan(&count); err != nil {
		t.Fatalf("count events: %v", err)
	}
	return count
}

func TestPreparedStatementInTransaction(t *testing.T) {
	db := openTestDB(t, "CREATE TABLE check_events (check_id INTEGER NOT NULL, action TEXT NOT NULL)")
	insertCheck(t, db, 101, true)

	ctx := context.Background()
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		t.Fatalf("begin tx: %v", err)
	}
	defer tx.Rollback()

	stmt, err := tx.PrepareContext(ctx, "INSERT INTO check_events(check_id, action) VALUES (?, ?)")
	if err != nil {
		t.Fatalf("prepare statement: %v", err)
	}
	defer stmt.Close()

	actions := []string{"pre_check", "disabled", "audit_logged"}
	for _, action := range actions {
		if _, err := stmt.ExecContext(ctx, 101, action); err != nil {
			t.Fatalf("exec prepared stmt for %s: %v", action, err)
		}
	}

	if err := tx.Commit(); err != nil {
		t.Fatalf("commit tx: %v", err)
	}

	if got := eventCount(t, db, 101); got != 3 {
		t.Fatalf("expected 3 events inserted via prepared statement, got %d", got)
	}
}

func TestConnectionPoolStatsObservation(t *testing.T) {
	db := openTestDB(t, "CREATE TABLE check_events (check_id INTEGER NOT NULL, action TEXT NOT NULL)")

	stats := db.Stats()
	if stats.MaxOpenConnections != 1 {
		t.Fatalf("expected MaxOpenConnections = 1, got %d", stats.MaxOpenConnections)
	}

	// Khi không có truy vấn đang chạy, InUse phải bằng 0.
	if stats.InUse != 0 {
		t.Fatalf("expected InUse = 0, got %d", stats.InUse)
	}
}

func TestSchemaMigrationOrderingAndRollback(t *testing.T) {
	dsn := fmt.Sprintf(
		"file:%s_migration?mode=memory&cache=shared",
		strings.ReplaceAll(t.Name(), "/", "_"),
	)
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		t.Fatalf("open sqlite: %v", err)
	}
	db.SetMaxOpenConns(1)
	defer db.Close()

	ctx := context.Background()

	// 1. Tạo bảng quản lý schema version 1
	initSQL := `
	CREATE TABLE schema_migrations (
		version INTEGER PRIMARY KEY,
		applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	CREATE TABLE endpoints (
		id INTEGER PRIMARY KEY,
		name TEXT NOT NULL
	);
	INSERT INTO schema_migrations (version) VALUES (1);
	`
	if _, err := db.ExecContext(ctx, initSQL); err != nil {
		t.Fatalf("init schema v1: %v", err)
	}

	// 2. Thử nghiệm migration lỗi: DDL thay đổi schema nhưng rollback
	txRollback, err := db.BeginTx(ctx, nil)
	if err != nil {
		t.Fatalf("begin failing migration: %v", err)
	}
	defer txRollback.Rollback()

	alterFail := "ALTER TABLE endpoints ADD COLUMN failed_col TEXT"
	if _, err := txRollback.ExecContext(ctx, alterFail); err != nil {
		t.Fatalf("alter table in failing tx: %v", err)
	}
	// Giả lập lỗi trước khi hoàn tất ghi version -> chủ động rollback
	if err := txRollback.Rollback(); err != nil {
		t.Fatalf("rollback failing migration: %v", err)
	}

	// Xác minh bằng chứng rollback: cột failed_col không tồn tại
	if hasColumn(t, db, "endpoints", "failed_col") {
		t.Fatalf("expected failed_col to be rolled back")
	}
	var verAfterRollback int
	err = db.QueryRowContext(
		ctx,
		"SELECT MAX(version) FROM schema_migrations",
	).Scan(&verAfterRollback)
	if err != nil {
		t.Fatalf("get version after rollback: %v", err)
	}
	if verAfterRollback != 1 {
		t.Fatalf("expected version 1 after rollback, got %d", verAfterRollback)
	}

	// 3. Migration v2 hợp lệ: thêm cột description và commit thành công
	txCommit, err := db.BeginTx(ctx, nil)
	if err != nil {
		t.Fatalf("begin migration v2: %v", err)
	}
	defer txCommit.Rollback()

	alterOK := "ALTER TABLE endpoints ADD COLUMN description TEXT"
	if _, err := txCommit.ExecContext(ctx, alterOK); err != nil {
		t.Fatalf("alter table: %v", err)
	}
	recVer := "INSERT INTO schema_migrations (version) VALUES (2)"
	if _, err := txCommit.ExecContext(ctx, recVer); err != nil {
		t.Fatalf("record version 2: %v", err)
	}
	if err := txCommit.Commit(); err != nil {
		t.Fatalf("commit migration v2: %v", err)
	}

	// 4. Xác minh version hiện tại là 2 và cột description tồn tại
	var currentVersion int
	err = db.QueryRowContext(
		ctx,
		"SELECT MAX(version) FROM schema_migrations",
	).Scan(&currentVersion)
	if err != nil {
		t.Fatalf("get current version: %v", err)
	}
	if currentVersion != 2 {
		t.Fatalf("expected current version = 2, got %d", currentVersion)
	}
	if !hasColumn(t, db, "endpoints", "description") {
		t.Fatalf("expected description column to exist in endpoints")
	}
}

func hasColumn(t *testing.T, db *sql.DB, table, col string) bool {
	t.Helper()
	rows, err := db.Query(fmt.Sprintf("PRAGMA table_info(%s)", table))
	if err != nil {
		t.Fatalf("pragma table_info: %v", err)
	}
	defer rows.Close()

	for rows.Next() {
		var cid int
		var name, colType string
		var notNull, pk int
		var dflt sql.NullString
		err := rows.Scan(&cid, &name, &colType, &notNull, &dflt, &pk)
		if err != nil {
			t.Fatalf("scan pragma: %v", err)
		}
		if name == col {
			return true
		}
	}
	return false
}

func TestCacheAsideStaleReadOnInvalidationFailure(t *testing.T) {
	db := openTestDB(t, "CREATE TABLE check_events (check_id INTEGER NOT NULL, action TEXT NOT NULL)")
	insertCheck(t, db, 202, true)

	// Mô phỏng bộ nhớ đệm in-memory
	cache := map[int64]bool{
		202: true, // Cache đang giữ enabled = true
	}

	ctx := context.Background()

	// 1. Database cập nhật trạng thái thành công
	if err := Disable(ctx, db, 202); err != nil {
		t.Fatalf("Disable() error = %v", err)
	}

	// 2. Giả lập tình huống xóa cache (invalidation) gặp lỗi mạng / timeout
	invalidationFailed := true
	if !invalidationFailed {
		delete(cache, 202)
	}

	// 3. Chứng minh bất đồng nhất (stale read):
	// Database đã là false, nhưng cache vẫn trả về true!
	dbEnabled := checkEnabled(t, db, 202)
	cachedEnabled := cache[202]

	if dbEnabled != false {
		t.Fatalf("expected dbEnabled = false, got %v", dbEnabled)
	}
	if cachedEnabled != true {
		t.Fatalf("expected cachedEnabled = true, got %v", cachedEnabled)
	}
	// Đây chính là bằng chứng thực tế: DB transaction không thể tự động bảo đảm
	// tính nguyên tử cho một hệ thống cache bên ngoài.
}
