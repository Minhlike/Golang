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
