package fixed

import (
	"context"
	"database/sql"
	"database/sql/driver"
	"errors"
	"sync/atomic"
	"testing"
)

var lostCommitReply = errors.New("injected lost commit reply")

// A legacy driver deliberately lacks ConnBeginTx. Its remote outcome is only
// a model, not a real database experiment; database/sql lifecycle is real.
type contractDriver struct{ state *contractState }
type contractState struct{ begins, commits, rollbacks atomic.Int32 }
type contractConnector struct{ driver *contractDriver }
type contractConn struct{ state *contractState }
type contractTx struct{ state *contractState }

func (d *contractDriver) Open(string) (driver.Conn, error)               { return &contractConn{d.state}, nil }
func (c contractConnector) Connect(context.Context) (driver.Conn, error) { return c.driver.Open("") }
func (c contractConnector) Driver() driver.Driver                        { return c.driver }
func (c *contractConn) Prepare(string) (driver.Stmt, error)              { return nil, errors.New("prepare unused") }
func (c *contractConn) Close() error                                     { return nil }
func (c *contractConn) Begin() (driver.Tx, error) {
	c.state.begins.Add(1)
	return &contractTx{c.state}, nil
}
func (tx *contractTx) Commit() error   { tx.state.commits.Add(1); return lostCommitReply }
func (tx *contractTx) Rollback() error { tx.state.rollbacks.Add(1); return nil }

func contractDB(t *testing.T) (*sql.DB, *contractState) {
	t.Helper()
	s := new(contractState)
	db := sql.OpenDB(contractConnector{&contractDriver{s}})
	t.Cleanup(func() { _ = db.Close() })
	return db, s
}

func TestCommitErrorDoesNotMakeDeferredRollbackUndoCommit(t *testing.T) {
	db, s := contractDB(t)
	tx, err := db.BeginTx(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	if err := tx.Commit(); !errors.Is(err, lostCommitReply) {
		t.Fatalf("Commit = %v", err)
	}
	if err := tx.Rollback(); !errors.Is(err, sql.ErrTxDone) {
		t.Fatalf("Rollback after Commit = %v", err)
	}
	if s.commits.Load() != 1 || s.rollbacks.Load() != 0 {
		t.Fatalf("driver calls: commits=%d rollbacks=%d", s.commits.Load(), s.rollbacks.Load())
	}
}

func TestUnsupportedIsolationDoesNotSilentlyBeginDefault(t *testing.T) {
	db, s := contractDB(t)
	tx, err := db.BeginTx(context.Background(), &sql.TxOptions{Isolation: sql.LevelSerializable})
	if err == nil || tx != nil {
		if tx != nil {
			_ = tx.Rollback()
		}
		t.Fatal("unsupported isolation silently accepted")
	}
	if s.begins.Load() != 0 {
		t.Fatal("unsupported isolation reached legacy Begin")
	}
}
