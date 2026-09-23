# Lab Part 21 — Reconciliation Controller & Rate-Limited Workqueue

Lab này hiện thực hóa hoàn chỉnh mô hình **Controller Pattern** và **Vòng lặp điều hòa (Reconciliation Loop)** chuẩn công nghiệp trong Go, kế thừa tư duy từ Kubernetes `client-go/util/workqueue` nhưng độc lập, tối giản và tự chủ hoàn toàn qua standard library:

1. **`queue/` (WorkQueue):**
   - Hàng đợi đa luồng hỗ trợ Deduplication (gộp các sự kiện trùng lặp trên cùng một resource key).
   - Serialized processing per key (khóa `processing` set, đảm bảo tại một thời điểm chỉ có tối đa 1 worker reconcile một key).
   - Exponential Backoff Rate Limiting (`AddRateLimited`) với cấu hình `BaseDelay`, `MaxDelay` và `MaxRetries` ngăn chặn bão retry (retry storm) khi tài nguyên đích gặp sự cố.

2. **`controller/` (Controller Runtime & Self-Healing Reconciler):**
   - Worker pool cố định, nhận tín hiệu từ queue và thực thi hàm `Reconcile(ctx, key)`.
   - Tính Lũy Thừa (Idempotency): Reconcile đưa hệ thống từ Actual State về Desired State; nếu trạng thái đã chuẩn thì là no-op.
   - Graceful shutdown đồng bộ qua `sync.WaitGroup` và `sync.Cond`.

## Kiểm thử và vận hành

```powershell
go test -v ./...
go test -race ./...
go vet ./...
```
