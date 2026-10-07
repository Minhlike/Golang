# Lab — Transaction boundary

`database/sql` là standard library. Lab thêm `modernc.org/sqlite` chỉ làm
driver SQLite thuần Go để contract chạy hoàn toàn cục bộ; không cần Docker,
database server hay credential. Cùng API `database/sql` sẽ dùng driver và
dialect khác khi chương trình thật cần PostgreSQL.

## Nhiệm vụ

Mở `exercise/disable_test.go`, rồi tự tạo implementation cho:

```go
func Disable(ctx context.Context, db *sql.DB, checkID int64) error
```

Nó phải tắt check và ghi event `disabled` trong **một** transaction. Bốn test
chốt contract: commit đủ hai thay đổi, check không tồn tại, event bị từ chối
phải rollback update, và `nil` database bị từ chối ở boundary.

```powershell
go test -tags exercise ./exercise
go test -race -tags exercise ./exercise
```

Đừng mở `fixed/` trước lượt tự làm đầu tiên. Khi test xanh, so với reference:

```powershell
go test ./fixed
go test -race ./fixed
```

## Những điểm cần tự quyết định

- Mở transaction bằng `BeginTx(ctx, nil)`.
- Đặt rollback cleanup ngay sau khi có `tx`; chỉ `Commit` khi mọi statement đã
  thành công.
- Gọi cả `UPDATE` lẫn `INSERT` qua `tx`, không gọi lại `db` ở giữa.
- Dùng argument binding thay vì ghép `checkID` vào SQL string.
- Phân biệt không có row với failure hạ tầng bằng error contract riêng.

Test dùng SQLite có chủ đích để chứng minh atomicity. Placeholder `?`,
constraint và concurrency behavior của driver này không phải specification của
mọi database.

## Retry không nằm trong contract hiện tại

`TestDisableRepeatedCallRecordsAnotherAuditEvent` chạy `Disable` hai lần và
chốt hai audit event. Đây không phải lỗi của transaction: mỗi lượt đều atomic.
Nó là chứng cứ rằng API của lab chưa hứa retry-safe. Nếu product cần “cùng một
operation chỉ ghi một lần”, API phải nhận operation identity (ví dụ idempotency
key) và schema phải giữ identity đó bằng một quy tắc như unique constraint.

## Các ranh giới mở rộng trong kiểm thử

- **Prepared statement trong transaction (`TestPreparedStatementInTransaction`):**
  Minh họa `tx.PrepareContext(ctx, query)` và trách nhiệm gọi `stmt.Close()`.
  Prepared statement gắn chặt với vòng đời transaction và tối ưu khi lặp lại câu
  lệnh nhiều lần.
- **Quan sát connection pool (`TestConnectionPoolStatsObservation`):**
  Sử dụng `db.Stats()` để theo dõi `MaxOpenConnections`, `InUse`, `Idle` và
  hiểu cơ chế cấp phát tài nguyên của pool manager.
- **Thứ tự migration và rollback DDL (`TestSchemaMigrationOrderingAndRollback`):**
  Lưu trữ schema version trong bảng quản lý, áp dụng thay đổi tuần tự và kiểm chứng
  khả năng rollback DDL khi gặp lỗi (xác nhận cột hủy không tồn tại và version giữ nguyên).
- **Bất đồng nhất cache (`TestCacheAsideStaleReadOnInvalidationFailure`):**
  Chứng minh ranh giới tách biệt giữa cache và database: DB commit thành công
  nhưng cache invalidation thất bại sẽ dẫn đến đọc dữ liệu cũ (stale read). DB
  transaction không thể tự động bảo đảm tính nguyên tử cho hệ thống cache bên ngoài.
