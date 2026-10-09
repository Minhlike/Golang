// Package outbox is a single-owner dispatcher teaching lab, not a broker.
package outbox

import (
	"context"
	"database/sql"
	"errors"
	"net/url"
	"path/filepath"
	"strings"

	_ "modernc.org/sqlite"
)

var ErrConflict = errors.New("operation key has a different payload")

type Event struct {
	Key   string
	Delta int
}

type Store struct{ db *sql.DB }

// Open owns a local database file. PRAGMAs apply to every new connection.
func Open(ctx context.Context, path string) (*Store, error) {
	abs, err := filepath.Abs(path)
	if err != nil {
		return nil, err
	}
	p := filepath.ToSlash(abs)
	if !strings.HasPrefix(p, "/") {
		p = "/" + p
	}
	u := url.URL{Scheme: "file", Path: p}
	q := url.Values{}
	for _, pragma := range []string{
		"busy_timeout(5000)", "foreign_keys(1)",
		"journal_mode(DELETE)", "synchronous(FULL)",
	} {
		q.Add("_pragma", pragma)
	}
	u.RawQuery = q.Encode()
	db, err := sql.Open("sqlite", u.String())
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	s := &Store{db: db}
	_, err = db.ExecContext(ctx, `
CREATE TABLE IF NOT EXISTS balance (
 id INTEGER PRIMARY KEY CHECK(id=1),
 total INTEGER NOT NULL CHECK(total BETWEEN 0 AND 1000000000)
);
INSERT OR IGNORE INTO balance VALUES(1,0);
CREATE TABLE IF NOT EXISTS operations (
 key TEXT PRIMARY KEY, delta INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
 key TEXT PRIMARY KEY REFERENCES operations(key),
 delta INTEGER NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('pending','completed'))
);
CREATE TABLE IF NOT EXISTS inbox (
 key TEXT PRIMARY KEY, delta INTEGER NOT NULL
);`)
	if err != nil {
		db.Close()
		return nil, err
	}
	return s, nil
}

func (s *Store) Close() error { return s.db.Close() }

func valid(e Event) bool {
	return e.Key != "" && len(e.Key) <= 128 && e.Delta > 0 && e.Delta <= 100
}

// Apply writes business state and the obligation to send in the SAME tx.
// checkpoint is fault-injection wiring only; production callers pass nil.
func (s *Store) Apply(ctx context.Context, e Event, checkpoint func(string)) error {
	return s.apply(ctx, e, checkpoint, false)
}

// BrokenApply commits without the event; death in the gap loses the obligation.
func (s *Store) BrokenApply(ctx context.Context, e Event, checkpoint func(string)) error {
	return s.apply(ctx, e, checkpoint, true)
}

func hit(f func(string), name string) {
	if f != nil {
		f(name)
	}
}

func (s *Store) apply(ctx context.Context, e Event, checkpoint func(string), broken bool) error {
	if !valid(e) {
		return errors.New("invalid event")
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	// Acquire the write lock before reading; no read-to-write upgrade race.
	r, err := tx.ExecContext(ctx,
		`INSERT INTO operations VALUES(?,?) ON CONFLICT(key) DO NOTHING`, e.Key, e.Delta)
	if err != nil {
		return err
	}
	n, err := r.RowsAffected()
	if err != nil {
		return err
	}
	var prior int
	if err = tx.QueryRowContext(ctx, `SELECT delta FROM operations WHERE key=?`, e.Key).Scan(&prior); err != nil {
		return err
	}
	if prior != e.Delta {
		return ErrConflict
	}
	if n == 1 {
		if _, err = tx.ExecContext(ctx, `UPDATE balance SET total=total+? WHERE id=1`, e.Delta); err != nil {
			return err
		}
		if !broken {
			if _, err = tx.ExecContext(ctx, `INSERT INTO outbox VALUES(?,?,'pending')`, e.Key, e.Delta); err != nil {
				return err
			}
		}
	}
	hit(checkpoint, "before_commit")
	if err = tx.Commit(); err != nil {
		return err
	}
	hit(checkpoint, "after_commit")
	if broken && n == 1 {
		_, err = s.db.ExecContext(ctx, `INSERT INTO outbox VALUES(?,?,'pending')`, e.Key, e.Delta)
	}
	return err
}

// Receive atomically deduplicates identity and its business effect on the
// receiving side. A separate receiver file models a separate transaction.
func (s *Store) Receive(ctx context.Context, e Event) error {
	if !valid(e) {
		return errors.New("invalid event")
	}
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	r, err := tx.ExecContext(ctx,
		`INSERT INTO inbox VALUES(?,?) ON CONFLICT(key) DO NOTHING`, e.Key, e.Delta)
	if err != nil {
		return err
	}
	n, err := r.RowsAffected()
	if err != nil {
		return err
	}
	var prior int
	if err = tx.QueryRowContext(ctx, `SELECT delta FROM inbox WHERE key=?`, e.Key).Scan(&prior); err != nil {
		return err
	}
	if prior != e.Delta {
		return ErrConflict
	}
	if n == 1 {
		if _, err = tx.ExecContext(ctx, `UPDATE balance SET total=total+? WHERE id=1`, e.Delta); err != nil {
			return err
		}
	}
	return tx.Commit()
}

// DeliverOne assumes exactly one dispatcher owner, including across processes.
// Pending is recoverable: no RAM lease or processing flag can hide an event.
// A crash after send retries that event. Send may have an ambiguous outcome.
func (s *Store) DeliverOne(ctx context.Context, send func(context.Context, Event) error, checkpoint func(string)) (bool, error) {
	if send == nil {
		return false, errors.New("sender is required")
	}
	var e Event
	err := s.db.QueryRowContext(ctx,
		`SELECT key,delta FROM outbox WHERE state='pending' ORDER BY key LIMIT 1`).Scan(&e.Key, &e.Delta)
	if errors.Is(err, sql.ErrNoRows) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if err = send(ctx, e); err != nil {
		return false, err
	}
	hit(checkpoint, "after_send")
	_, err = s.db.ExecContext(ctx, `UPDATE outbox SET state='completed' WHERE key=?`, e.Key)
	return err == nil, err
}

type Snapshot struct{ Total, Pending, Completed, Operations, Received int }

func (s *Store) Snapshot(ctx context.Context) (Snapshot, error) {
	var v Snapshot
	err := s.db.QueryRowContext(ctx, `SELECT total,
 (SELECT COUNT(*) FROM outbox WHERE state='pending'),
 (SELECT COUNT(*) FROM outbox WHERE state='completed'),
 (SELECT COUNT(*) FROM operations), (SELECT COUNT(*) FROM inbox)
 FROM balance WHERE id=1`).Scan(&v.Total, &v.Pending, &v.Completed, &v.Operations, &v.Received)
	return v, err
}
