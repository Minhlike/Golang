# Independent scientific review — checkpoint Ch02 / Ch16 / Ch26 / Ch27

Trạng thái: **CHECKPOINT, chưa nghiệm thu toàn sách**. Bốn manuscript đã được đọc; các kết luận được kiểm chứng ở phạm vi chủ đề, source và test ghi dưới đây. Không suy ra rằng mọi claim trong bốn chương, hay mọi trang PDF, đã được xác minh. Các chương còn lại và hai Atlas chưa được review khoa học thủ công. Không có merge hoặc promotion Master.

## Baseline và phạm vi bảo toàn

`BASELINE_HEAD=5938862b864b51d755209031972a1bb07f5babf2`; source local/origin khớp sau fetch. Nhánh riêng `content/agent1-master-scientific-review`, worktree `D:/Golang-agent1-review`. Worktree Agent 2 ở `D:/Golang` giữ nguyên branch/HEAD và sạch. `main` / `origin/main` ở `bb00a9ad33e3cd5115928dc3542d2ce66c8d08d8` tại kiểm tra đầu lượt; không merge hai nhánh này.

| Artifact thực đã mở | Trang | SHA-256 | Trang render đã quan sát ở checkpoint |
| --- | ---: | --- | --- |
| A — `book/publication/Golang_Master_baseline_f2211520.pdf` | 493 | `f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09` | 15, 37, 207, 367, 380 |
| B — `book/print_ready/02_RUOT_SACH_GOLANG_525TRANG_A4.pdf` | 525 | `685b0b7a51ed9d3ab5a9b531f040a4ed24132d94142972811d3b47e52daeaa8f` | 15, 37, 230, 396, 409 |
| C — `Golang_Master.pdf` | 593 | `7dfedd9825d36ccfb57515311829bc163bb6eb746423487488419400c36d8b68` | 40, 275, 447, 458, 471 |

A được lưu bởi `6d08943ff4028f0a396c569b3c9dad27a6c68a34`; B được lưu bởi `b6fb26af83fecfcd204f95891edc3f85587a578c`. Toàn bộ 31 chapter file và hai Atlas có source giống nhau giữa hai commit đó; đây là đối chiếu blob Git, không phải kết luận đã đọc mọi câu trong hai PDF. Trang A37/B37 cho thấy cùng giải thích slice; A367/B396 cho thấy cùng code verifier cũ. Sự tăng trang A→B không chứng minh tăng tri thức. C có rewrite source trên cả 33 file; cần đánh giá từng thay đổi, không dùng số trang hay tỷ lệ tiếng Việt để chấp nhận.

`MASTER PROMPT.txt`, glossary, báo cáo Agent 2 đã đọc. Các lab memory leak/reliability đã tích hợp không bị sửa; hồi quy `part10-resource-retention` và `projects/opsprobe` được chạy mới. Không suy từ hồi quy này rằng đã review khoa học toàn bộ Ch10/12/13/20/23.

## Đối chiếu theo chương và cụm kiến thức

Cột A→B dưới đây là source tại hai commit đã nêu. `IDENTICAL_SOURCE` không phải một loại content gain. Cột B→C chỉ phân loại những chủ đề đã đối chiếu thủ công; `UNREVIEWED` là chưa có kết luận, không phải không có lỗi.

| Chương / tài liệu | A→B | B→C: kết luận hiện có | Review khoa học tiếp theo |
| --- | --- | --- | --- |
| Ch00 lịch sử | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch00 mở cửa | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch01 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch02 | IDENTICAL_SOURCE | EDITORIAL_REWRITE phần slice/ownership; CONTENT_REGRESSION ở cách gọi aliasing và assignment/pass-by-value | Đã kiểm chứng các contract bên dưới; chưa audit mọi claim runtime/UTF-8 |
| Ch03 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch04 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch05 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch06 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch07 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch08 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch09 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch10 | IDENTICAL_SOURCE | UNREVIEWED | Chưa review benchmark/profile; chỉ chạy lab retention bảo toàn |
| Ch11 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch12 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch13 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch14 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch15 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch16 | IDENTICAL_SOURCE | EDITORIAL_REWRITE phần signals; CONTENT_REGRESSION ở dịch idempotent và cardinality | Đã kiểm chứng recorder, window, instrumentation boundary và quan hệ span |
| Ch17 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch18 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch19 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch20 | IDENTICAL_SOURCE | UNREVIEWED | Chưa review chương; hồi quy opsprobe không thay thế việc đọc |
| Ch21 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch22 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch23 | IDENTICAL_SOURCE | UNREVIEWED | Real API không chạy trong checkpoint này |
| Ch24 | IDENTICAL_SOURCE | UNREVIEWED | Không chạy cloud |
| Ch25 | IDENTICAL_SOURCE | UNREVIEWED | Cần kiểm tra HMAC/MAC với chữ ký số trong lượt tiếp nối |
| Ch26 | IDENTICAL_SOURCE | EDITORIAL_REWRITE phần trust boundary; CONTENT_REGRESSION do dịch exact error; code không khớp lab là lỗi kế thừa từ A/B | Đã kiểm chứng model, delegation, dừng tuần tự và bài tập contract |
| Ch27 | IDENTICAL_SOURCE | EDITORIAL_REWRITE phần kernel; hook sys_enter_execve vẫn đúng ở A/B/C, không phải lỗi mới | Đã kiểm chứng decoder/reader giả và các giới hạn hook; chưa compile/load BPF thật |
| Ch28 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Ch29 | IDENTICAL_SOURCE | UNREVIEWED | Chưa đọc manuscript |
| Library Atlas | IDENTICAL_SOURCE | UNREVIEWED | Chưa review source guides thủ công |
| Error Atlas | IDENTICAL_SOURCE | UNREVIEWED | Validator cấu trúc không thay review từng diagnostic |

CONTENT_GAIN trong checkpoint mới là phản ví dụ có test cho capacity/copy nông, SLI tích lũy/cửa sổ, timeout wrapper và test kiểm chứng parent span cụ thể. Không gán nhãn CONTENT_GAIN cho một đoạn dài hơn hoặc một gloss song ngữ mới.

## 15 ví dụ trước / sau và bằng chứng

Các số dòng là source của checkpoint này. “Cũ” chỉ rõ lỗi kế thừa khi có; không quy mọi lỗi cho Agent 2.

| ID / mức | File:dòng | Cũ → mới | Lý do và phép kiểm chứng |
| --- | --- | --- | --- |
| R01 / P2 | `book/chapters/02-gia-tri-slice-va-aliasing.md:37,184` | “phép gán … pass-by-value”; “trùng tên bộ nhớ” → phép gán sao chép giá trị, đối số truyền theo giá trị; sửa vùng nhớ dùng chung | Aliasing không phải đụng tên biến. Đối chiếu đặc tả slice và assignment; test chia sẻ phần tử giữ nguyên. |
| R02 / P2 | `book/chapters/02-gia-tri-slice-va-aliasing.md:66`; `book/VIETNAMESE_TECH_TERMS.md:51` | 24 byte đã gắn amd64 nhưng chưa có phép đo; scope dịch cả “phạm vi sống” → đo kèm toolchain/GOOS/GOARCH, không tính backing array; scope là phạm vi định danh | Runtime pin `slice.go:16–20`; test đo Windows/amd64/Go1.27.1: slice=24, uintptr=8. Không đặt 24 thành language guarantee, không lẫn scope/lifetime. |
| R03 / P2 | `book/chapters/02-gia-tri-slice-va-aliasing.md:172`; `labs/part2-values/main.go:8` | Ghi `preview[0]` vô điều kiện (lỗi đã có trước C) → guard độ dài, contract rỗng rõ | Test mới trên source baseline panic `index out of range`; bản sửa test/vet/race đạt. Không hứa giữ tính nil. |
| R04 / P2 | `book/chapters/02-gia-tri-slice-va-aliasing.md:196–209` | Dễ suy “cap=len/copy thì độc lập” → phản ví dụ cap chỉ chặn append; copy pointer vẫn chia sẻ pointee | `TestCapacityLimitDoesNotIsolateExistingElements`, `TestPointerElementsRemainSharedAfterCopy`, test quyền sửa cả hai phía. Không thêm lab trùng retention đã có. |
| R05 / P3 | `book/chapters/16-thay-duoc-he-thong.md:5–13` | “tường thuật chuẩn xác… ngữ nghĩa bản chất… (*incident*)/(*event*)/(*counter*)” → câu hỏi vận hành cụ thể, mô hình phép chiếu, boundary bộ đếm | Đọc thủ công giữ quan hệ xu hướng/chi tiết và ba outcome. Không sweep song ngữ toàn sách, không dùng quota từ để tuyên bố prose tốt. |
| R06 / P2 | `book/chapters/16-thay-duoc-he-thong.md:109–111` | “mẫu số thất bại… lũy thừa bất biến” → Completed gồm mọi kết quả; lũy đẳng thuộc retry, không đổi timeout thành success | Recorder thật tăng Completed+TimedOut; giải thích ambiguous completion phía server vẫn được giữ. Lỗi nghĩa denominator đã có ở A/B; cách dịch idempotent sai xuất hiện ở C. |
| R07 / P2 | `book/chapters/16-thay-duoc-he-thong.md:35` | Cardinality = “số lượng chiều nhãn” → số chuỗi phân biệt từ tổ hợp giá trị nhãn | Một `request_id` vẫn có thể sinh nhiều chuỗi. Tập outcome của lab không đổi; không lấy URL/ID làm label. |
| R08 / P2 | `book/chapters/16-thay-duoc-he-thong.md:113–117` | Chỉ nhắc recorder không có window → 1000 thành công + 10 timeout cho 99,01% lifetime nhưng 0% cửa sổ mới | Test số cụ thể không chờ đồng hồ; nêu giả định cùng recorder chưa reset, uint64 underflow, gap và ngoại suy increase. Không tự viết collector. |
| R09 / P2 | `book/chapters/16-thay-duoc-he-thong.md:181`; `labs/part16-real-signals/probeapi/server_test.go:65` | “Handler hoàn tất”, test chỉ Parent.IsValid → ghi metric trước response; assert đúng Parent SpanID và TraceID của request | Đọc handler đầy đủ. Test không chỉ chứng minh có một parent bất kỳ; metric/log không xác nhận client nhận response. |
| R10 / P2 | `book/chapters/26-chuoi-cung-ung-co-the-kiem-chung.md:14–20`; `assets/diagrams/supply-chain-policy-evidence.puml:6–20` | Intro nói tích hợp SLSA/govulncheck; source hình gắn admission với “SLSA Level 3+”; raster 4096px cắt các chặng sau → model cục bộ và hình tham chiếu đủ sáu chặng, không chứng nhận Build L3 | Giữ phản ví dụ self-asserted key/issuer. Đối chiếu SLSA v1.2 và Cosign; xem trực tiếp C447 xác nhận hình bị cắt. Dựng lại bằng PlantUML có sẵn 1.2024.7, UTF-8, size limit 8192; PNG mới 1400×2368 không bị cắt. Candidate được kiểm riêng; không coi BuilderID hay ALLOW là chứng cứ đạt cấp độ. |
| R11 / P1 | `book/chapters/26-chuoi-cung-ung-co-the-kiem-chung.md:280–350` | Verifier bỏ qua interface; lỗi chữ ký vẫn `return true` rồi chạy provenance (đã có A/B) → delegate và `return res` ngay mỗi chốt lỗi | Không sửa policy.go để hợp thức hóa sách. Code Markdown thực được ghép với phần support đã công bố và chạy toàn bộ test lab, gồm StopsOnSignatureFailure. |
| R12 / P2 | `book/chapters/26-chuoi-cung-ung-co-the-kiem-chung.md:212–225,267,292,333` | “missing chứng thực nguồn gốc `SLSA` attestation”, shortened diagnostics → exact error từ source; tiêu đề/comment VerifyDigest từ “xác thực artifact/bất biến” → chỉ kiểm định dạng chuỗi | Test excerpt đạt; không dịch identifier/error, không coi regex là đối chiếu nội dung artifact. Các format vulnerability giữ Package và Symbol; Reachable trong bảng là fixture, không phải call graph đã chạy. |
| R13 / P1 | `book/chapters/26-chuoi-cung-ung-co-the-kiem-chung.md:414–506`; `labs/part26-supply-chain-gate/contract_examples.go` | Catalog có thể đồng ý digest sai; callback nil/canceled trả nil vẫn ALLOW → validate digest, guard callback/context trước và sau | Test dữ liệu biên và mutant bỏ post-check bị bắt. Context không preempt callback không hợp tác; không tuyên bố bảo đảm force-timeout hay verify dịch vụ thật. |
| R14 / P2 | `book/chapters/27-quan-sat-linux-bang-ebpf-va-go.md:51,360–421,456,466,542`; `labs/part27-ebpf-observer/observer_test.go` | Snippet thiếu nhánh/source Reason; cancellation có thể trước Read; mô tả buffer/argv quá dễ suy rộng → giữ nhánh thật, đồng bộ Read entry, phân biệt attempt với success, buffer hữu hạn và empty argv | Reader giả block/Close có test race mới; đường `/var/tmp`, dash/bash và nmap được test. Kernel compile/load/attach vẫn NOT_RUN. Thêm NULL-check không có nghĩa Clang chỉ kiểm cú pháp hay verifier chấp nhận mọi tính chất khác. |
| R15 / P2 | `scripts/build_pdf.py:464–536,741–762`; `scripts/test_review_heading_contract.py:44–89` | H4 rơi vào paragraph, PDF C275 in nguyên `####`; câu dẫn ở candidate 46 tách khỏi code 47; candidate trung gian 468 bỏ lại heading trong khi intro+code sang 469 → dùng minor heading có sẵn và flatten heading/intro/code trong cùng nhóm giữ trang | Regression kiểm H4/code hashes, câu dẫn có/không blank line, code một/nhiều chunk và heading trước intro dài trên PDF nhỏ thực. Mutant bỏ flatten tái hiện heading orphan và test bắt được. Giữ font/palette/cover/layout system; pagination có thể đổi toàn sách, không phải chỉ bốn chương. |

Nguồn kỹ thuật cho phần đã sửa: [Go specification — slices](https://go.dev/ref/spec#Slice_types) và [append/copy](https://go.dev/ref/spec#Appending_and_copying_slices); source runtime Go1.27.1 cục bộ; [Prometheus increase](https://prometheus.io/docs/prometheus/latest/querying/functions/#increase); [SLSA v1.2 Build track](https://slsa.dev/spec/v1.2/build-track-basics) và [Cosign verification](https://docs.sigstore.dev/cosign/verifying/verify/); [BPF verifier](https://docs.kernel.org/bpf/verifier.html) và [ring buffer](https://docs.kernel.org/bpf/ringbuf.html); [bpf2go upstream](https://github.com/cilium/ebpf/tree/v0.22.0/cmd/bpf2go). Link không thay thế một lần chạy thật.

## Evidence và các gate

`book/evidence/agent1-scientific-review/verify.py` tái chạy test/race/vet ở bảy module, 25 renderer tests, excerpt Ch26, ba negative controls trong thư mục tạm hoặc tiến trình riêng, diff check, validators cấu trúc và PDF scope checks. `validation.json` chứa command, cwd, exit code, source SHA, stdout/stderr dạng UTF-8 giải mã và base64 byte gốc + checksum. Không gọi văn bản đã chuẩn hóa là stdout nguyên byte. EXPECTED_FAILURE của đối chứng âm tách khỏi PASS. Không lấy exit 0 của code-width CLI làm kết luận: script gọi hàm validator và kiểm số violation thực.

| Gate | Trạng thái tại checkpoint | Phạm vi / giới hạn |
| --- | --- | --- |
| 1 Baseline integrity | VERIFIED_ARTIFACTS, SOURCE_MAPPING_LIMITED | Hash/page count/history và các trang đã mở nêu trên; không giả nhận review toàn A/B/C |
| 2 Semantic diff | PARTIAL | Có bảng mọi chương; chỉ các chủ đề Ch02/16/26/27 đã có phán đoán thủ công |
| 3 Scientific correctness | SCOPED_REPAIRS_TESTED; WHOLE_BOOK_PENDING | Hai lỗi P1 đã biết trong phần đang sửa đã xử lý; số P0/P1 chưa phát hiện ở phần chưa review là UNKNOWN, không phải 0 |
| 4 Pedagogical value | SCOPED_EVIDENCE | Phản ví dụ số nhỏ, dự đoán và contract test; không template hóa các chương |
| 5 Code & lab regression | SCOPED_PASS | Evidence mới kết thúc 2026-10-11 04:25:56 UTC: bảy module test/race ×3 + vet, 25 renderer tests, tám excerpt từ Markdown và PDF, ba EXPECTED_FAILURE đúng signature; validators/diff check đạt |
| 6 Language quality | PARTIAL_MANUAL_REVIEW | Sửa dịch sai và một số đoạn trọng điểm; không claim hết song ngữ/slop toàn sách |
| 7 PDF content parity | SCOPED_BODY_CHECKS_PASS; WHOLE_BOOK_PENDING | 25 chương không sửa + hai Ch00 + hai Atlas bằng nhau sau normalization; 58 raster occurrences bảo toàn trừ một hình sửa có phép so pixel riêng; TOC/bookmark 29 chương khớp heading. Cover parity không đạt; visual chỉ 34/604 trang, không promotion |

## Checkpoint để tiếp nối

Không bắt đầu lại từ các nhãn PASS của Agent 2. Tiếp nối từ branch này sau khi xác minh HEAD/status và hash candidate trong evidence. Bốn manuscript đã đọc không đồng nghĩa mọi dependency/live path đã kiểm chứng. Cần tiếp tục đọc Ch00/01/03–15/17–25/28/29 và hai Atlas; hoàn thiện semantic diff theo từng chủ đề, rà benchmark/profile và thuật ngữ theo ngữ cảnh. Live Sigstore/SLSA/govulncheck, BPF và Operator API không được tự đổi thành PASS.

Tình trạng candidate và trang thực đã mở sẽ được chốt ở mục kết quả cuối dưới đây. Root Master/rollback, MASTER PROMPT, nhánh main/design và nội dung memory leak/reliability giữ nguyên. Báo cáo lịch sử Agent 2 được giữ để đối chiếu; các tuyên bố “SLSA L3”, `sched_process_exec`, “cilium/ebpf biên dịch C” ở dòng 115–119 của báo cáo đó không được coi là bằng chứng.

## Kết quả cuối của checkpoint

Candidate cuối được build bằng `scripts/build_pdf.py --candidate-only`: **604 trang**, SHA-256 `de5c877c5bc88d2923f2103019bee26efe472935685c5d3483e91e784882e8e3`. Đây là candidate của nhánh reviewer, không phải Master đã nghiệm thu. Các render từ candidate trung gian không được dùng làm bằng chứng visual của bản này.

Đã mở trực tiếp 34 trang của đúng candidate cuối bằng Poppler 144 DPI, từng ảnh riêng ở độ phân giải 1191×1684: **1, 2, 40, 45, 46, 47, 277, 279, 283, 284, 287, 288, 289, 455, 456, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 480, 491, 492, 493, 494, 495, 496, 499, 500**. Quan sát code, bảng, heading, hình, dấu tiếng Việt, ngắt trang và folio ở phạm vi đó. 33 trang nội dung/mục lục không còn lỗi clipping hay orphan đã phát hiện trong mốc sửa; trang 1 có giới hạn parity nêu dưới đây. **570 trang còn lại chưa được mở của bản cuối**, không được gán VISUAL_PASS.

Hình 46 ở trang 456 hiện đủ sáu chặng, caption nằm cùng trang và không còn phần bị cắt ở mép phải. PNG trang đã xem có SHA-256 `23be823202a4d5b41654725d287da086d2ddd1dda5cf5a2770e95e1561dea520`; manifest chỉ cập nhật entry của hình này. Không kế thừa trạng thái review cũ của những hình khác. Tiêu đề mục 7 ở trang 471 được giữ cùng intro và command; ở candidate trung gian nó bị bỏ lại ở trang 468. Test tái hiện lỗi trước sửa đã thất bại đúng assertion; mutant trong evidence giữ phép kiểm chứng đó có thể chạy lại.

Trang 1 của candidate dùng title page do renderer tạo, **không tái tạo full-bleed cover đã promotion riêng của baseline C**. Không sửa nhánh thiết kế, không coi cover parity là đạt và không promotion candidate. Root `Golang_Master.pdf` vẫn SHA-256 `7dfedd9825d36ccfb57515311829bc163bb6eb746423487488419400c36d8b68`; rollback vẫn `685b0b7a51ed9d3ab5a9b531f040a4ed24132d94142972811d3b47e52daeaa8f`. `MASTER PROMPT.txt` không đổi: trong worktree riêng SHA-256 `45da2eb45b88d36fb5cfc95b63547b01274d618b8b8c6256efce4766f2c34785`, trong worktree gốc `bd93e286595e9b45812b09d40124966137300d010fe19d063b860a564947d125`; hai checkout có byte hash khác nhau, Git diff không có thay đổi file này.

Các mục R01–R15 là **15 nhóm phát hiện**, gồm 2 nhóm P1, 12 nhóm P2 và 1 nhóm P3 đã xử lý ở phạm vi nêu rõ. Không phát hiện P0 trong những phần đã kiểm chứng; không suy ra P0/P1 toàn sách bằng 0. Các lab thay đổi là part2-values, part16-observability-evidence, part16-real-signals, part26-supply-chain-gate và part27-ebpf-observer. Memory leak/reliability giữ nguyên source; hồi quy của hai module liên quan không thay thế kiểm định khoa học những chương đó.

Evidence mới hoàn tất lúc **2026-10-11 04:25:56 UTC**, exit code 0: **24 command có kết quả thành công và 3 EXPECTED_FAILURE đúng exit/signature**, không có thất bại ngoài dự kiến. Go1.27.1 Windows/amd64; bảy module `test -race -count=3 ./...` và `vet ./...` đạt. 25 renderer tests đạt. Tám Go excerpt Ch26 từ Markdown và từ chính PDF được compile/test với test lab, mỗi bộ chạy race ba lần. 34 Go block của bốn chương có token đúng thứ tự trong PDF; đây không phải kiểm byte nguyên trạng cho toàn sách. Code-width có **0 violation**; Error Atlas, zero-bullet và character-art validators đạt. Gofmt không còn file cần format; diff toàn mốc và staged diff sạch lỗi whitespace.

TOC được extract độc lập và đối chiếu heading: **29/29**; bookmark chapter destination **29/29**. 25 chương không sửa, hai Ch00 và hai Atlas có text normalization khớp baseline C; normalization bỏ whitespace/folio/H4 marker, nên không thay thế kiểm copy code. Inventory **58/58** body raster occurrences có pixel RGB bảo toàn, ngoại trừ Hình 46 được thay bằng đúng asset mới; cover nằm ngoài phép kiểm này. Không có claim rằng đã scan grayscale, overlap hay cross-reference trên mọi trang.

Tái lập trên nhánh này: dùng Go đã pin cùng gcc cho race, Python với dependencies của workspace; chạy `scripts/build_pdf.py --candidate-only`, sau đó `book/evidence/agent1-scientific-review/verify.py`. Evidence giữ hash source và raw output; PDF build có thể có SHA khác khi chạy lại, phải chốt hash/render của artifact mới nếu dùng để nghiệm thu. `FINAL_STATUS=CHECKPOINT_ONLY`; nghiệm thu khoa học/PDF toàn sách vẫn **PENDING**, các live path vẫn **NOT_RUN**. Không merge main/design, không publication acceptance.
