# Reliability failure paths — nghiệm thu phạm vi nguồn và lab

## Regression finalization — 2026-10-09

STARTING_HEAD=00ba2f315f06a5d287e676ab214df40978f79e0c
TESTED_HEAD=eb1714e7ba335d3f222932dea041467d1c8d5c4b
BRANCH=content/reliability-failure-paths
PDF_UNCHANGED=YES
PDF_SHA256=f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09

Đây là kết quả kiểm thử mới, không phải lần chạy lại quy trình xuất bản.
36 command đạt điều kiện đã khai báo: 29 PASS, 5 EXPECTED_FAILURE,
1 NOT_RUN (Windows integration stub), 1 COMPILE_ONLY (Linux cross-compile).
Không tính SKIP hay mutant đỏ là test contract PASS. Test/vet/race đã chạy
cho TLS/mTLS (part11), outbox (part13), opsprobe/failurelab, Operator fake
(part23), resource retention (part10); không sửa resource retention lab.
Identity, outbox, failurelab mỗi package lặp 20 lần. Workload được bật bằng
RUN_BOUNDED_LOAD=1 trong 20 lần lặp failurelab và thêm 20 lần workload có race.

Workload giữ measurement và fault injection hiện có. Sau join consumer và
runner, kiểm tra accepted+rejected=64, completed+dropped=accepted,
running=queue=0, peakRunning<=4, peakQueue<=16. Contract graceful drain yêu cầu
dropped=0, số kết quả nhận bằng completed và channel results đã đóng. Mutant
lost_completion_count chỉ giảm một đơn vị trên COPY của Stats sau join:
exit 1 tại `workload completion accounting`, không gây leak hoặc sửa runner.
Ba mutant cũ split_commit, uncancellable_send, trust_equals_role cũng exit 1
đúng assertion. Không đặt ngưỡng latency/RSS hay yêu cầu thứ tự scheduler.

### Evidence có thể tái tạo

[validation.json](validation.json) schema 2 lưu chính xác bytes của output
stdout/stderr đã hợp nhất trong `combined_output_base64`, cùng SHA-256;
`combined_output_text` chỉ là bản decode UTF-8 với replacement nếu cần.
[validation.log](validation.log) là transcript để đọc: expand tab, bỏ trailing
whitespace và chuẩn hóa newline thành LF. Log này KHÔNG phải stdout nguyên byte.
Hai artifact được sinh cùng một lượt; command, cwd, environment overrides,
exit, marker, thời lượng và result label được lưu cho từng bước, kể cả lỗi.

Ở 00ba2f3, validation.json được tạo trước lần bổ sung trường stdout vào harness;
harness đã đổi nhưng artifact không được regenerate theo schema ấy. Vì vậy
JSON đã commit không có stdout, dù verify.py cùng commit có dòng thêm trường.
Không thể khôi phục bytes gốc từ transcript đã chuẩn hóa; lượt mới capture bytes
thật, không tự điền output cũ. Mọi con số ở mục lịch sử bên dưới thuộc 00ba2f3,
không phải timing của lượt mới. Log lịch sử đọc bằng
`git show 00ba2f3:book/evidence/reliability-failure-paths/validation.log`.

Harness kiểm tra ancestry và `git diff --check ba251160..TESTED_HEAD` với SHA
đã resolve; không chỉ kiểm working tree sạch. Nó kiểm index bằng
`git diff --cached --quiet`, chạy `--cached --check` nếu có staged changes;
lượt này index rỗng nên staged check trong JSON là NOT_RUN. Staged evidence mới
được kiểm riêng trước commit. Final commit range được kiểm riêng sau commit,
gồm cả `00ba2f3..HEAD` và `ba251160..HEAD`. Fingerprint các input đã test và
checksum PDF được ghi trước/sau lượt chạy. Commit sau TESTED_HEAD chỉ cập nhật
evidence và README integration; không thay code đã test. Không yêu cầu artifact
chứa SHA của chính commit evidence đang chứa nó.

637 file ngoài phạm vi được đối chiếu SHA-256 với snapshot đầu lượt: 0 mismatch,
bao gồm chapter, MASTER, PDF và WIP book/design, research. Main vẫn 1cc60d9;
design/catalog-2026 vẫn 0737345. Không đổi dependency hay merge/build PDF.

### Operator: API thật đã chạy, không suy rộng sang cluster đầy đủ

REAL_API_STATUS=INTEGRATION_TESTED. Ubuntu-24.04/WSL chạy Kubernetes v1.37.0,
etcd 3.7.0 từ [release controller-tools chính thức](https://github.com/kubernetes-sigs/controller-tools/releases/tag/envtest-v1.37.0).
Archive Linux amd64 được đối chiếu SHA-512 với
[manifest chính thức](https://raw.githubusercontent.com/kubernetes-sigs/controller-tools/HEAD/envtest-releases.yaml);
checksum archive và từng binary được lưu trong JSON. Harness re-extract archive
đã xác minh trước khi chạy, không tin binary cũ nằm cạnh archive.

Test tạo control plane riêng và cleanup Stop; create/root update không ghi
status, status update giữ spec/generation, spec update tăng generation 1→2,
observedGeneration vẫn 1 và stale resourceVersion bị conflict. Mutant
root_status_write exit 1 tại `status writer contract`. API PASS có marker
`INTEGRATION_TESTED owned real API`; Windows SKIP và cross-compile vẫn mang
nhãn riêng, không được dùng để suy ra API PASS.

Sửa ownership guard: envtest v0.25.1 đọc USE_EXISTING_CLUSTER khi pointer
UseExistingCluster nil. Test nay đặt pointer false rõ ràng; harness còn xóa
KUBECONFIG/TEST_ASSET_* và ép USE_EXISTING_CLUSTER=false khi chạy. Không dùng
cluster/cloud hay kubeconfig của người dùng. Envtest không có scheduler,
kubelet, GC controller hoặc external finalizer; các năng lực ấy chưa được test.

Tái lập từ D:/Golang sau khi tải archive chính thức vào đường dẫn dưới:

```powershell
python book/evidence/reliability-failure-paths/verify.py `
  --go D:/Golang/.tools/go1.27.1/bin/go.exe `
  --wsl-distro Ubuntu-24.04 `
  --envtest-archive D:/Golang/.tools/reliability-envtest-1.37.0/envtest-v1.37.0-linux-amd64.tar.gz
```

Không có blocker trong phạm vi regression finalization. Dừng tại đây để quyết
định merge; không mở wave mới hoặc chứng nhận production/publication readiness.

## Milestone gốc 00ba2f3 — hồ sơ lịch sử, không phải kết quả lượt mới

BASELINE_HEAD=ba25116038d35d86ef138fbb089d9094a614ded8
BRANCH=content/reliability-failure-paths
CHAPTERS_CHANGED=11,13,16,20,23,25,28
LABS_CHANGED=part11-request-path/identity; part13-transaction-boundary/outbox;
part23-controller-runtime-operator/integration; projects/opsprobe/failurelab
PDF_UNCHANGED=YES
PDF_SHA256=f2211520a13e878a275546e6aa1519c1d0d32fb665caa224f95efe1dc566ce09

Không build PDF, không đổi MASTER/renderer/style/design branch, không merge
main. Các chapter chỉ có insertion; không xóa hay thay đoạn memory leak cũ.
619 file ngoài 7 chapter được phép bổ sung đã đối chiếu SHA-256 với snapshot
trước sửa, gồm tracked file và WIP `book/design`, `research`: 0 mismatch.
Source branch vẫn ba251160; main vẫn 1cc60d9; design vẫn 0737345.

### Bằng chứng và lệnh kiểm định của milestone gốc

validation.json và validation.log ở commit 00ba2f3 ghi command/cwd/environment/
exit code cùng transcript đã chuẩn hóa, không phải output nguyên byte. Go 1.27.1 windows/amd64,
Windows 11 build 26200, CGO/race bằng GCC hiện có trên PATH. Không thêm hay đổi
go.mod/go.sum; tất cả module tests dùng dependency đã pin. Harness ban đầu có
lỗi tên thư mục part25; đã sửa và chạy lại toàn bộ harness, không lấy lần
chạy bị ngắt làm kết quả cuối.

Trong transcript, chín dòng help của CLI đã mở tab thành spaces để qua staged
whitespace check; không đổi nội dung diagnostic. Metadata của lượt chạy ghi
41/41 command đạt điều kiện exit/marker, trong đó ba command đỏ là
EXPECTED_FAILURE và API prerequisite SKIP vẫn là NOT_RUN. Staged diff --check
được chạy riêng sau khi đưa cả evidence mới vào index, không chỉ kiểm tệp cũ.

```powershell
# Từ D:/Golang; dùng Python và reportlab/font assets hiện có
$env:PYTHONPATH = 'D:/Golang/.workspace/qa-toolchain/pydeps'
python book/evidence/reliability-failure-paths/verify.py `
  --go D:/Golang/.tools/go1.27.1/bin/go.exe
```

Test, vet, race trên 8 module: part11, part13, opsprobe, part23, part16,
part25-github-automation, part28 và part10-resource-retention. Ba package mới
outbox/identity/failurelab được test lặp 20 lần. Sau bổ sung assertion cleanup
queue, chạy thêm `go test -count=5 -race -timeout=60s ./failurelab` và
`go vet ./failurelab`: exit 0. Zero-bullet, code-width, Error Atlas,
character-art và diagram encoding validators, git diff --check đều exit 0.
Code width: 0 dòng overflow. Không gọi đây là visual/publication QA.

Chốt cleanup: consumer goroutine của workload được join cả trên đường failure,
không chỉ normal path. Trên source cuối, `RUN_BOUNDED_LOAD=1 go test -count=1
-race -timeout=60s ./failurelab` chạy toàn package gồm load và exit 0 (4.859s);
`go vet ./failurelab` exit 0. Những con số workload dưới đây vẫn trích từ lượt
được lưu trong validation.log của 00ba2f3, không lấy timing của race làm benchmark.

## 1. Crash consistency và identity bền vững

Sự cố: business state đã commit nhưng outbox chưa được ghi. Child chết ở
checkpoint after_commit; bản `split_commit` giữ Total=7, Operations=1,
Pending=0. Chính `TestOutboxContract` exit 1 tại assertion yêu cầu pending
event, không phải compile error: `EXPECTED_FAILURE`.

Bản sửa ghi operation, balance và pending cùng transaction. Process death
trước commit, sau commit trước response, và sau receiver commit trước sender
completion đều kiểm tra bằng child exit 77. Database reopen/dispatcher restart
ở connection/process mới, cùng identity không tăng số dư lần nữa; conflict
payload bị từ chối. Cuối các case: sender Total=7, Completed=1, Operations=1;
receiver Total=7, Received=1. Hai connection cạnh tranh cùng key cũng chỉ tạo
một operation. Test acknowledgment mất ghi 2 attempts, 1 effect.

`UNIT_TESTED` cho validation/idempotency/concurrency;
`REAL_LOCAL_VERIFIED` cho SQLite file, subprocess chết và reopen. Receiver
durable dùng SQLite riêng nhưng sender gọi trực tiếp, không kiểm broker/network
delivery thật. At-least-once cần tiếp tục dispatch; không có exactly-once
delivery, power-loss proof, retention policy hay multi-dispatcher fencing.

## 2. Suy giảm dưới tải và cancellation

Sự cố: consumer dừng đọc, HTTP xong nhưng worker bị giữ ở send. Mutant
`uncancellable_send` exit 1 tại assertion cancellation phải giải phóng handoff;
cleanup mở rescue rồi join worker: `EXPECTED_FAILURE`.

Bản sửa giới hạn workers/queue, shed admission đầy, deadline tính từ admission,
send nghe cancellation và giải phóng queued payload trước Done. Fixture worker
2/queue 2 nhận 4 job và từ chối 100; completed=4, running=0, queue=0,
peakRunning=2, peakQueue=2. Consumer-stop test còn kiểm tra dropped queued job.
Response hold/release, deadline, 503, body truncated và cut connection đều đi
qua HTTP loopback thật; outcome được đối chiếu với log, histogram và OTel span.
Handler không hợp tác phải được release riêng dù caller đã cancel/join.

Workload hữu hạn đã chạy: attempts=64, accepted/completed=20, rejected=44,
elapsed=205.7433ms, throughput=97.21/s, probe p50=949600ns,
p95=101531100ns; timeout rate=0.30, failure rate=0.35 trên completed;
rejection rate=0.6875 trên attempts. Peak running=4, peak queue=16,
running/queue cuối=0, dropped=0. Đây là output của lượt trong validation.log ở 00ba2f3,
không là threshold hay capacity production. Heap/goroutine snapshots không
chuẩn hóa sau GC, không chứng minh retention, RSS hay scheduler pressure.

`UNIT_TESTED` cho bounds, budget và cleanup; `REAL_LOCAL_VERIFIED` cho network
local/log/metric/span. Fault fixture không phải incident production; không
retry, không Internet/cloud. Trace CPU/scheduler và soak dài chưa được đo;
chapter chỉ hướng dẫn chọn chúng khi giả thuyết cần bằng chứng tương ứng.

## 3. Danh tính mạng và contract của hạ tầng

Sự cố: mọi certificate được CA tin ký bị coi là quyền ghi. Mutant
`trust_equals_role` cho reader HTTP 200/effect=1 và làm
`TestAuthorizationContract` exit 1: `EXPECTED_FAILURE`.

Bản sửa lấy URI identity của verified chain rồi xét action. TLS thật từ chối
CA/SAN sai, thiếu client cert, client CA lạ, expired client, wrong EKU. Reader
đọc được nhưng không ghi, identity lạ/thiếu bị 403, header X-Role không nâng
quyền; operator được phép ghi. Runtime-generated certificates/key ở RAM,
loopback và stdlib: `REAL_LOCAL_VERIFIED`; missing/unverified chain policy:
`UNIT_TESTED`. Không kiểm rotation/revocation/proxy/OAuth/MCP HTTP production.

Operator fake generation test: `MOCK_VERIFIED`, spec update giữ generation=1,
không đóng vai server. Test API thật đã có CRD/status schema và assertions
create/root/status isolation, generation/observedGeneration, stale RV conflict;
mutant root_status_write được chuẩn bị nhưng **NOT_RUN**.

Linux test cross-compile exit 0: COMPILE_ONLY. Test binary còn chạy trên
Ubuntu-24.04 qua WSL bằng:

```powershell
wsl -d Ubuntu-24.04 --exec `
  /mnt/d/Golang/.workspace/reliability-envtest.test `
  '-test.run=^TestRealAPIContract$' '-test.v'
```

Output: `NOT_RUN: set KUBEBUILDER_ASSETS to owned Kubernetes 1.37.x Linux
assets`, SKIP, exit 0. Windows stub cũng SKIP/NOT_RUN. Không dùng chữ PASS ở
footer suite để nhận đã test control plane. Docker/kind/kubectl không trên
PATH; không thấy Go/kube-apiserver/etcd hay thư mục assets ở WSL đã kiểm tra.
Pinned envtest còn có lỗi compile helper signal trên Windows; source API test
chỉ build Linux. Không sửa dependency hay cài cluster để che giới hạn này.

Lệnh API integration/mutant đủ prerequisite nằm trong lab README. Envtest
không chứng minh scheduler/kubelet/garbage collector/finalizer external side
effect. Chưa kiểm API thật là giới hạn công khai được nhiệm vụ cho phép, không
phải một integration assertion đã nghiệm thu.

## Điểm dừng

Ba chuỗi fault/broken oracle/fix/recheck đã hoàn thành trong phạm vi có thể
chạy local; bài API integration sẵn sàng tái lập nhưng NOT_RUN. Evidence này
không chứng nhận production readiness hay tính in được của PDF. Không mở wave
mới, không rebuild PDF và không merge main.
