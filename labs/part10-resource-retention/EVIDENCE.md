# Bằng chứng thực nghiệm resource retention

Ngày chạy: 2026-10-09, Windows/amd64. Binary fixture được build bằng Go 1.27.1 từ `cmd/investigate`, standard library only. MemProfileRate=1. Không đo RSS. Không đặt threshold số liệu vào unit test. Profile sinh cục bộ dưới `artifacts/1.27.1/` và bị gitignore; dữ liệu chọn dưới đây lấy từ stdout và `go tool pprof` thực sự đã chạy, không phải expected output.

## Workload và chuỗi quan sát

Slice/cache/churn/goroutine/ticker: `-cycles=4 -items=2 -bytes=4194304 -limit=2`, chạy mỗi mode/bản trong một process mới. Mode goroutine/ticker không dùng payload bytes. Với mọi mode, điểm đo 0 trước tải; điểm 1–4 sau mỗi chu kỳ; điểm 5 sau cleanup. Sau mỗi điểm đo đã hoàn thành hai lượt GC. Xem README cho lệnh tương đương; ở lượt này `-out=artifacts/1.27.1/<mode>-<baseline|fixed>`.

| Mode/bản | Entry chu kỳ 1→4 | Goroutine chu kỳ 0→5 | HeapAlloc chu kỳ 1→4 (byte) |
| --- | --- | --- | --- |
| slice/baseline | 2,4,6,8 | 1,1,1,1,1,1 | 8753352,17147136,25535840,33924560 |
| slice/fixed | 2,4,6,8 | 1,1,1,1,1,1 | 369888,369984,370112,370160 |
| cache/baseline | 2,4,6,8 | 1,1,1,1,1,1 | 8753744,17147480,25536104,33929936 |
| cache/fixed | 2,2,2,2 | 1,1,1,1,1,1 | 8753928,8759152,8759184,8764280 |
| churn/đối chứng | 0,0,0,0 | 1,1,1,1,1,1 | 369920,369936,369952,369968 |
| goroutine/baseline | 0,0,0,0 | 1,3,5,7,9,1 | 366680,373536,375408,377168 |
| goroutine/fixed | 0,0,0,0 | 1,1,1,1,1,1 | 366792,372464,373040,374304 |
| ticker/baseline | 0,0,0,0 | 1,3,5,7,9,1 | 367720,375824,383320,385608 |
| ticker/fixed | 0,0,0,0 | 1,1,1,1,1,1 | 367288,372832,374352,375616 |

Không diễn giải mọi byte HeapAlloc là payload. Churn với `-fixed` cũng đã chạy, không thay logic, HeapAlloc chu kỳ 1→4: 369920,375032,375032,380272. Chênh lệch nền giữa process là lý do không assert mức heap.

Slice baseline chu kỳ 4: HeapAlloc=33924560, HeapInuse=34316288, HeapSys=41680896, HeapReleased=4235264, TotalAlloc=42968000. Sau cleanup ở chu kỳ 5: HeapAlloc=369936, HeapInuse=761856, HeapSys=41680896, HeapReleased=4694016, TotalAlloc=45330936. HeapSys không giảm cùng object; đây không phải phép đo RSS hoặc bằng chứng collector còn giữ payload sống.

## Profile xác nhận allocation site

Đọc `04.heap.pprof` với `-inuse_space` và `-alloc_space`. Các dòng payload dưới đây là **flat** tại vị trí cấp phát, không phải tổng toàn process; MB/kB là đơn vị hiển thị của pprof. `32768kB` bằng 32 MiB, `0.12kB` là cách pprof làm tròn 128 byte.

| Mode/bản | Site | inuse_space | alloc_space |
| --- | --- | --- | --- |
| slice/baseline | main.payload | 32768kB | 32MB |
| slice/fixed | main.payload | Không còn site payload sống trong kết quả lọc | 32MB |
| slice/fixed | fixed.Prefix | 0.12kB | Không dùng làm tiêu chí kết luận |
| cache/baseline | main.payload | 32MB | 32MB |
| cache/fixed | fixed.(*Cache).Put | 8MB | 32MB |
| cache/fixed | main.payload | Không còn site payload sống trong kết quả top | 32MB |
| churn/đối chứng | main.payload | Không còn site payload sống trong kết quả top | 32MB |

Lệnh lọc slice fixed đã chạy: `go tool pprof -inuse_space -top -nodefraction=0 '-focus=main.payload|fixed.Prefix' artifacts/1.27.1/slice-fixed/04.heap.pprof`. Nó hiển thị flat 0.12kB ở fixed.Prefix, không có main.payload. Profile cho allocation site; source Prefix xác nhận view vẫn dẫn tới backing array ở baseline, còn fixed copy các byte.

Goroutine dump chu kỳ 4: tám worker baseline receive chờ ở `baseline.Wait.func1` (`[chan receive]`, retention.go dòng 32); tám worker ticker chờ ở `baseline.RunTicker.func1` (`[select]`, dòng 51). Không dùng goroutine ID/địa chỉ làm contract. Các parent đã cancel trước đo, baseline không quan sát ctx.Done. Harness có rescue nên cả hai mode trở về một goroutine sau cleanup.

## Context: goroutine count không bắt được mọi retention

Lượt riêng: `-mode=context -cycles=4 -items=128`, child timeout một giờ; `-bytes` không dùng. `-out=artifacts/1.27.1/context512-baseline` và `context512-fixed`. Cả hai luôn NumGoroutine=1. HeapAlloc chu kỳ 1→4 của baseline là 411656,459248,494304,543440 byte; fixed là 365160,370272,370304,375512 byte. Sau hủy parent: 385016 và 375256 byte.

Lệnh đã chạy cho profile 04 của hai bản và 05 của baseline:

```powershell
go tool pprof -inuse_objects -top -nodefraction=0 `
  '-focus=context.WithDeadlineCause' `
  artifacts/1.27.1/context512-baseline/04.heap.pprof
```

Flat tại context.WithDeadlineCause: baseline/04=1024 object; fixed/04 không có object trực tiếp tại site; baseline/05 không còn object trực tiếp tại site. Những allocation con vẫn có vài object ở time.newTimer/parent trong profile; không gọi count ấy là số context hoặc khẳng định mọi timer đã được GC thu hồi ngay. Source đúng tag giải thích parent registration và timer; test kiểm child.Err sau operation, parent cancellation và deadline đã qua mà không assert heap.

## Giới hạn

Đây là fixture nhỏ được đo có chủ đích, không benchmark production. Profiling/dump làm TotalAlloc tăng; full sampling và forced GC thay chi phí chạy. Chưa đo Linux, RSS/working set, lưu lượng HTTP thật hoặc deadline dài chạy đủ một giờ. Các số byte/site/object không ổn định giữa compiler/runtime/platform. Bằng chứng quan trọng là đường giữ và contract sau sửa, không số absolute.

Version check: source local `time/tick.go` xác nhận unreferenced ticker GC và Stop không close; `internal/godebugs/table.go` ghi `asynctimerchan` Removed=27. Đối chiếu release notes chính thức 1.27 xác nhận timer channel luôn đồng bộ, không còn switch behavior cũ như giai đoạn 1.23–1.26.

## Kết quả kiểm định

| Phạm vi đã chạy | Kết quả |
| --- | --- |
| Lab mới, Go 1.27.1 và 1.27.2 windows/amd64 | `go test -count=1 ./...`, `go vet ./...`, `go test -race -count=1 ./...`: PASS trên cả hai |
| 12 test fixed, lặp 40 lượt trên từng toolchain | PASS; không dùng threshold heap/RSS |
| 2 test CLI | PASS; từ chối cấu hình ngoài budget; chạy cả sáu mode/baseline/fixed và ghi profile tại thư mục tạm |
| Lab cũ part2-values, part3-data-models, part9-workflow-pressure, part10-measure-first, part12-service-lifecycle | test/vet/race PASS trên Go 1.27.1; source không thay đổi |
| `go vet ./testdata/lostcancel` | Diagnostic như dự kiến, exit khác zero: `the cancel function returned by context.WithCancel should be called, not discarded, to avoid a context leak` |
| `go test -tags exercise ./exercise` trước implementation | Compile failure như dự kiến: chưa có Prefix/NewCache/Wait/DoTimeout/RunTicker |
| Manuscript | Code width PASS (0 dòng tràn), zero-bullet PASS, Error Atlas PASS (85 ID giữ nguyên), character-art=0 |
| Diagram/asset guards | Encoding, semantics và visual manifest validators PASS; không sửa sơ đồ hoặc asset |
| Parser/renderer contract unit tests | 5 test manuscript diagram + 16 test publication contract PASS; không build production PDF |
| UTF-8 và Markdown fence | 17 source/lab file đọc strict UTF-8, không có marker lỗi; các fence cân bằng |

Các validator asset/renderer là regression checks, không phải visual QA của pagination mới. Theo scope yêu cầu, không rebuild hoặc thay `Golang_Master.pdf`. Nội dung mới chưa có trong PDF baseline. Tất cả số đo ở phần trên thuộc Go 1.27.1; kiểm thử trên 1.27.2 không làm chúng thành số đo của 1.27.2.
