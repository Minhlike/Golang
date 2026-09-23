# Chương 18 — Đưa thay đổi ra production

Sau Chương 17, ta có thể đặt một artifact có digest vào desired state. Nhưng một digest không tự trả lời artifact ấy đến từ source nào, đã đi qua test nào, job nào có quyền deploy, hay rollout xong có nghĩa gì với người dùng. Một pipeline xanh chỉ là tín hiệu về những bước nó đã chạy; nếu các bước không nói rõ contract, màu xanh tạo cảm giác an toàn mạnh hơn bằng chứng thực tế.

Mental model của chương là: **delivery là chuỗi bằng chứng gắn một source revision với một artifact bất biến, rồi cho phép promotion theo policy hẹp.** Pipeline không “đưa code lên production”. Nó build một artifact, ghi identity của artifact, thu evidence cho các gate đã định nghĩa, và chỉ một job có quyền phù hợp mới cập nhật desired state bằng chính digest ấy. Rollback cũng là một promotion có chủ đích tới artifact đã biết, không phải nút hoàn tác cho mọi side effect của hệ thống.

## Một commit xanh vẫn chưa là release

Giả sử một PR pass unit test. Sau đó runner build image, job deploy dùng tag `:main`, cluster pull image, và rollout hiện `3/3 Available`. Chuỗi này còn nhiều câu hỏi chưa được trả lời: image đang chạy có đúng là image vừa build không; source revision nào đã tạo image; credential deploy có quyền rộng đến đâu; `3/3` chỉ ra replica available hay chứng minh request business thành công; và nếu data migration đã chạy, rollback image có đảo dữ liệu lại không?

Đây không phải lý do để bỏ CI/CD vì “quá phức tạp”. Nó là lý do để mỗi bước hứa một điều nhỏ, kiểm chứng được. Source revision là identity của đầu vào source. Artifact digest là identity của output build. Test là evidence về behavior mà test bao phủ. Provenance là evidence về quan hệ build mà verifier đã xác nhận. Promotion policy quyết định evidence nào đủ để thay desired state. Rollout status là observation về controller và replica, không phải SLO.

![Chuỗi evidence của delivery](../../assets/diagrams/delivery-evidence-chain.png)
@figure Một delivery đáng tin là chuỗi contract hẹp. Mũi tên không biến test pass thành lời hứa về mọi failure mode.

@table Mỗi tín hiệu delivery cho phép kết luận đến đâu

| Evidence | Điều có thể nói | Điều chưa thể nói |
| --- | --- | --- |
| Commit/revision | Source input đã được chọn. | Artifact nào thật sự được build. |
| Image digest | Một artifact content-addressed cụ thể. | Artifact đó qua test hay provenance nào. |
| Test pass | Contract của test hiện có đã pass. | Toàn bộ behavior production, data hay dependency. |
| Rollout complete | Controller đã đạt điều kiện rollout của workload. | SLO, chi phí, hay business transaction của user. |

Tag dễ đọc vẫn có ích cho con người, nhưng tag là một tên có thể trỏ sang artifact khác theo thời gian. Promotion production nên mang digest mà gate đã xét, không rebuild “cùng commit” ở job sau rồi hy vọng hai output giống nhau. Nếu cần reproducibility cao hơn, build policy phải pin input phù hợp, ghi revision/toolchain và quản lý base image/dependency; digest chỉ nhận diện output, không tự giải thích output được tạo thế nào.

## Gate không phải nghi thức, mà là policy có người chịu trách nhiệm

Một pipeline tốt không bắt mọi thay đổi chạy toàn bộ suite đắt tiền chỉ vì dashboard thích nhiều ô xanh. Nó đặt gate theo risk và feedback loop. Static check hoặc unit test nhanh có thể chạy sớm trên mọi thay đổi. Integration test có dependency thật có thể chạy ở stage khác, với timeout và teardown rõ ràng. Build/push chỉ chạy khi source đã qua gate cần thiết. Promotion production cần identity bất biến, evidence được xác minh, permission hẹp và một đường rollback đã được diễn tập.

Cost guardrail cũng là một contract. Một job integration có thể tạo cluster tạm, registry storage hay egress; phải có owner, timeout, concurrency limit, cleanup và giới hạn phạm vi. “Tốn tiền” không tự làm một job sai, còn “CI xanh” không hợp thức hóa resource không có lifecycle. Hãy đo chi phí của stage nặng trước khi tối ưu, giống cách Chương 10 đặt benchmark trước khi đổi code.

> **Dừng để dự đoán:** Nếu build job pass nhưng không ghi digest vào promotion record, deploy job đang chứng minh điều gì khi nó pull `:main`? Nếu security scan báo sạch nhưng image deploy là output của một build khác, scan đã xét đúng artefact chưa?

Không có gate chung cho mọi sản phẩm. Một payment service có thể cần review/approval và contract test khác một CLI nội bộ. Điều cần giữ chung là policy không fail-open: evidence thiếu hoặc không hợp lệ phải dẫn đến từ chối promotion có giải thích, không âm thầm đổi tag hay dùng credential mạnh hơn để “chạy cho xong”.

## Quyền deploy là capability, không phải biến môi trường tiện tay

CI runner có thể chạy source và action mà workflow cho phép, nên credential deploy không nên xuất hiện ở mọi job. Với GitHub Actions, `GITHUB_TOKEN` nên bắt đầu bằng quyền đọc tối thiểu rồi tăng quyền tại job thực sự cần. Cloud credential dài hạn được chép vào secret là một boundary rủi ro khác: secret có thể bị dùng nhầm, log redaction không phải một bằng chứng tuyệt đối, và policy ở cloud mới quyết định token có làm được gì.

OIDC là một cách đưa capability về đúng job cần nó. Workflow xin identity token; cloud provider kiểm tra claim/trust condition rồi cấp access token ngắn hạn cho job. Nó không tự cấp quyền deploy: trust policy vẫn phải giới hạn repository, branch/tag hoặc environment, role và resource. `id-token: write` chỉ cho phép job xin token OIDC, không tự cho phép sửa cloud resource. Đó là lý do “bật OIDC” không thể thay thế review policy IAM.

~~~yaml
permissions:
  contents: read

jobs:
  deploy-production:
    permissions:
      contents: read
      id-token: write
    environment: production
~~~

Đoạn YAML chỉ mô tả **ý định phân quyền**, chưa phải workflow deploy chạy được: nó không định nghĩa cloud role, subject claim, approval rule, digest, action version hay command. Đừng copy snippet rồi thêm secret quyền admin để vượt qua bước trust. Thiết kế đúng phải viết từ resource mà job được phép thay đổi, identity của workflow được cloud tin, và điều kiện nào khiến token bị từ chối.

## Promotion phải giữ identity của artifact

Lab không ký image và không gọi registry. Nó giữ lại boundary quyết định: candidate có digest hợp lệ, revision để truy vết, test evidence và provenance evidence; thiếu gate trả một `Decision` từ chối, còn digest sai là input lỗi. Phân biệt hai case này giúp caller không biến configuration sai thành “release bị từ chối bình thường”.

~~~go
type Candidate struct {
	Digest             string
	Revision           string
	TestsPassed        bool
	ProvenanceVerified bool
}

type Decision struct {
	Allowed bool
	Digest  string
	Reason  string
}

func Evaluate(candidate Candidate) (Decision, error) {
	if !validDigest(candidate.Digest) {
		return Decision{}, ErrInvalidDigest
	}
	if strings.TrimSpace(candidate.Revision) == "" {
		return Decision{}, ErrMissingRevision
	}
	if !candidate.TestsPassed {
		return Decision{Reason: ReasonTestsNotPassed}, nil
	}
	if !candidate.ProvenanceVerified {
		return Decision{Reason: ReasonProvenanceMissing}, nil
	}
	return Decision{Allowed: true, Digest: candidate.Digest}, nil
}
~~~

`ProvenanceVerified` ở đây là input đã được verifier khác kiểm tra; bool này **không** mô hình hóa chữ ký, trust root, identity của builder hay policy admission. Đây là chủ ý sư phạm: trước khi dùng framework attestation hay API registry, ta cần thấy promotion decision phải giữ đúng digest và fail closed khi evidence vắng mặt. Một struct nhỏ không được phép giả vờ thay supply-chain system thật.

## Rollback là một release khác, không phải máy quay thời gian

Kubernetes Deployment có revision cho thay đổi Pod template và có thể rollout quay về revision trước. Nhưng revision không bao phủ mọi state ngoài Pod template: thay đổi `replicas` không tạo revision, history có thể bị dọn theo `revisionHistoryLimit`, external config có thể đã đổi, còn database migration và message đã gửi không tự đảo. Vì thế “rollback được” phải được nói thành câu cụ thể hơn: *rollback artifact/template nào, trong môi trường nào, với data contract và side effect nào?*

Một runbook rollback cần ít nhất: tiêu chí kích hoạt, digest/revision đã biết tốt, owner được phép promote, lệnh hay automation đã thử trong môi trường phù hợp, evidence sau rollout, và quyết định cho data. Nếu release mới chỉ đổi binary stateless, rollback có thể là promotion digest cũ rồi quan sát rollout. Nếu release đổi schema theo hướng không tương thích, rollback có thể cần feature flag, expand/contract migration hoặc dừng phát hành thay vì chạy `undo` ngay.

~~~text
rollback request
  -> chọn artifact/revision đã biết
  -> kiểm tra data và blast radius policy
  -> promote digest cũ
  -> quan sát rollout + signal
  -> ghi lại quyết định và kết quả
~~~

Đừng tự động rollback chỉ vì một metric chớp đỏ nếu policy chưa định nghĩa window, ownership và false-positive cost. Nhưng cũng đừng để “manual rollback” nghĩa là một người gõ tag tùy ý lúc incident. Cùng identity, gate và permission boundary của forward delivery phải được giữ khi quay lại.

## Case study: rollout xanh, user vẫn fail

Một release `sha256:abc...` pass unit và integration test, provenance đã verify, rồi được deploy bằng digest. Deployment báo complete: Pod mới available. Vài phút sau, availability SLI tụt vì config ở production trỏ tới endpoint dependency đã retire. Không evidence nào ở đây mâu thuẫn nhau:

- Build/promotion proof nói artifact và gate nào đã được dùng.
- Deployment status nói controller đã thay replica theo policy.
- SLI/log/trace của Chương 16 nói user path đang fail và giúp tìm cohort/config lệch.

Action đúng không phải kết luận “CI vô dụng” hay “Kubernetes đánh lừa mình”. Team kiểm tra blast radius, candidate config và data contract; nếu rollback digest cũ khôi phục khả năng phục vụ mà không phá migration, họ promote digest cũ theo runbook. Sau incident, gate cần được sửa ở boundary đã thiếu: configuration validation hoặc integration environment gần production hơn, không nhất thiết là thêm một security scan vô liên quan.

## Lab: tự viết admission decision fail-closed

Mở `labs/part18-promotion-evidence/exercise/admission_test.go` trước. Test không dùng network, registry, secret hay crypto library. Nó yêu cầu anh tự định nghĩa đúng sự khác nhau giữa candidate malformed và candidate hợp lệ nhưng chưa đủ evidence. Exercise đỏ vì `Evaluate` chưa được viết; fixed giữ implementation nhỏ để test các invariant trước khi bất kỳ CI vendor nào xuất hiện.

~~~powershell
cd labs/part18-promotion-evidence
go test -tags exercise ./exercise
go test ./fixed
go vet ./fixed
go test -race ./fixed
~~~

Sau khi làm xong, thử viết một test mới: nếu `TestsPassed` là false nhưng provenance true, `Decision` có được giữ digest hay không? Hãy chọn policy và diễn đạt lý do. Lab hiện chọn không giữ digest trong decision bị từ chối để caller không vô tình lấy identity đó đi deploy; policy khác chỉ hợp lệ khi được ghi rõ và có test riêng.

<!-- pagebreak -->

**Đáp án — chỉ đọc sau khi đã tự làm.** Validate digest rồi revision trước vì chúng là input contract. Sau đó kiểm tra từng gate và return decision từ chối không error; `error` dành cho candidate malformed. Chỉ decision allowed mới mang digest. `validDigest` chấp nhận đúng prefix `sha256:` và 64 chữ số hexadecimal thường; nó là validation định dạng, không phải xác thực content tồn tại hay chữ ký.

## Stage hai: chuỗi delivery từ commit đến promotion gate

Logic xét duyệt `Evaluate` ở trên cho ta thấy một quyết định promotion cần những
bằng chứng gì. Nhưng trong thực tế, các bằng chứng ấy không xuất hiện cùng lúc
trong một hàm Go đơn lẻ; chúng được tạo ra qua từng chặng của một pipeline phân
tán. `labs/part18-workflow-delivery` kết nối lý thuyết này vào một quy trình
hoàn chỉnh gồm ba phần: một workflow GitHub Actions mẫu (reviewable specimen),
một công cụ `promote-gate` bằng Go có thể chạy trong CI, và một cấu hình
Terraform thiết lập cầu nối OIDC với hạ tầng đám mây.

Để tránh những ngộ nhận tai hại trong vận hành, chuỗi delivery phải phân định
rõ bảy lớp thông tin kỹ thuật:

1. **Source revision:** Mã băm commit Git của mã nguồn đầu vào (ví dụ: `bcb3fe0`).
2. **Local image identity:** Tên/tag cục bộ hoặc Image Config ID (`.Id`) mà
   Docker daemon tạo ra trên máy build.
3. **Manifest digest:** Mã băm nội dung bất biến của OCI Image Manifest
   (`sha256:...`) bao gồm descriptor của mọi layer và config, được registry và
   Kubernetes dùng làm định danh duy nhất.
4. **Provenance:** Bản chứng thực (attestation) ghi nhận nguồn gốc commit,
   builder và công thức build.
5. **Verified evidence:** Kết quả xác minh chữ ký số của provenance từ công cụ
   chuyên trách; tuyệt đối không dùng cờ boolean giả mạo.
6. **Promotion decision:** Quyết định phê duyệt hoặc từ chối fail-closed dựa
   trên bằng chứng đã xác minh.
7. **Actual deployment:** Thao tác cập nhật desired state của workload bằng
   chính manifest digest đã được duyệt.

~~~text
Source Revision (git commit SHA)
      |
      v
Job: verify (test từng module: part16, part18)
      |
      v
Job: build-artifact (Docker Buildx metadata)
      |  --> phân biệt Image ID và OCI Manifest Digest
      v
Job: promote-production (environment: production)
      |  --> quyền id-token: write cho OIDC
      |  --> chạy promote-gate CLI (kiểm tra candidate)
      |  --> từ chối nếu thiếu verified evidence
      |  --> cập nhật desired state bằng manifest digest
~~~

### Workflow GitHub Actions mẫu và kiểm tra repo multi-module

Tệp `labs/part18-workflow-delivery/workflows/delivery.yaml` là tài liệu nghiên
cứu và kiểm tra mẫu (runnable specimen), không phải workflow đang kích hoạt trong
`.github/workflows/`. Nó minh họa các nguyên tắc thiết kế cốt lõi:

1. **Kiểm tra đúng từng Go module:** Repository của chúng ta gồm nhiều module
   độc lập và không có `go.work` ở root. Chạy `go test ./...` tại root sẽ thất
   bại hoặc vô nghĩa. Job `verify` dùng `working-directory` để chạy test, vet,
   và race detector riêng cho từng module thuộc delivery path:
   `labs/part16-real-signals` (service) và `labs/part18-workflow-delivery` (gate).
2. **Quyền mặc định chỉ đọc:** Khai báo `permissions: { contents: read }` ở cấp
   cao nhất. Quyền `id-token: write` chỉ được mở duy nhất ở job deploy.
3. **Ghim action bằng commit SHA bất biến:** Thay vì tag phiên bản có thể bị trôi,
   workflow ghim mã băm commit 40 ký tự đầy đủ của từng Action.
4. **Không đánh đồng Local Image ID với Manifest Digest:** Khi build cục bộ mà
   chưa push registry, Docker daemon chỉ lưu Image Config ID (`.Id`). Chỉ khi
   Buildx xuất metadata hoặc push lên registry, OCI Image Manifest Digest mới
   tồn tại để làm định danh bất biến cho promotion.

~~~yaml
# Trích đoạn từ workflows/delivery.yaml
permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      # Ghim commit SHA bất biến (v4.2.2 và v5.3.0)
      - uses: actions/checkout@11bd719... # v4.2.2
      - uses: actions/setup-go@3041d5d... # v5.3.0
        with:
          go-version: '1.27.1'
      # Kiểm tra từng module thuộc delivery path
      - name: Verify Service Module
        working-directory: labs/part16-real-signals
        run: |
          go test -v ./...
          go vet ./...
          go test -race ./...
      - name: Verify Gate Module
        working-directory: labs/part18-workflow-delivery
        run: |
          go test -v ./...
          go vet ./...
          go test -race ./...
~~~

### Thực thi Promotion Gate bằng Go và nguyên tắc Fail-Closed

Để biến policy admission thành một chốt chặn tự động trong pipeline, thư mục
`labs/part18-workflow-delivery/cmd/promote-gate` cung cấp một công cụ dòng lệnh
nhỏ gọn viết bằng Go. Công cụ này nhận các tham số đầu vào và trả về mã thoát
(exit code) chuẩn của hệ điều hành:

~~~powershell
cd labs/part18-workflow-delivery
go test -v ./...
go vet ./...
go test -race ./...
~~~

Trong pipeline CI, `tests-passed=true` được suy ra hợp lệ vì job `verify` phía
trước đã hoàn thành thành công trong đồ thị phụ thuộc (`needs: verify`). Tuy
nhiên, `provenance-verified` chỉ có thể là `true` khi đã có một bước xác thực
chữ ký số chuyên trách. Nếu stage này chưa có bước xác thực attestation thật, ta
**tuyệt đối không truyền cờ giả mạo `--provenance-verified=true`** (evidence
theater). Gate phải từ chối theo nguyên tắc fail-closed:

~~~powershell
# Định danh digest mẫu 64 ký tự hex
$DIGEST = "sha256:0123456789abcdef0123456789abcdef" + `
          "0123456789abcdef0123456789abcdef"

# 1. Thiếu provenance: gate từ chối fail-closed (Exit 1)
go run ./cmd/promote-gate `
  --digest $DIGEST `
  --revision "bcb3fe0" `
  --tests-passed=true `
  --provenance-verified=false

# 2. Đạt chuẩn khi có đủ cả test và provenance (Exit 0)
go run ./cmd/promote-gate `
  --digest $DIGEST `
  --revision "bcb3fe0" `
  --tests-passed=true `
  --provenance-verified=true

# 3. Trượt test: gate từ chối (Exit 1)
go run ./cmd/promote-gate `
  --digest $DIGEST `
  --revision "bcb3fe0" `
  --tests-passed=false `
  --provenance-verified=true

# 4. Định danh trôi nổi :latest: lỗi đầu vào (Exit 2)
go run ./cmd/promote-gate `
  --digest ":latest" `
  --revision "bcb3fe0"
~~~

Khi truyền `--digest ":latest"`, chương trình dừng ngay với thông báo:
`invalid candidate: digest must be a lowercase sha256 digest` và trả mã lỗi 2.

Đặc biệt, trong pipeline CI, khi `promote-gate` trả về mã lỗi (khác 0) do thiếu provenance hoặc trượt test, job quảng bá phải dừng ngay lập tức. Mọi cơ chế nuốt lỗi (như `|| echo` hay `continue-on-error`) để bước deploy tiếp tục chạy đều là "evidence theater": dựng gate cho có nhưng vẫn âm thầm phát hành code không kiểm chứng. Candidate bị gate từ chối đồng nghĩa với việc không có bất kỳ lệnh deploy nào được phép kích hoạt.

### Cầu nối AWS OIDC và Terraform: phân quyền tối thiểu thực chất

Mục `labs/part18-workflow-delivery/terraform/` cung cấp một cấu hình Terraform
minh họa mô hình liên kết danh tính OpenID Connect (OIDC) giữa GitHub Actions và
AWS IAM nhằm loại bỏ hoàn toàn các access key dài hạn tĩnh.

Cần hiểu đúng ranh giới của các cơ chế phân quyền trong cấu hình này:

1. **Khóa chặt claim `sub`:** Trust policy bắt buộc claim `sub` phải khớp chính
   xác `repo:Minhlike/Golang:environment:production`. Bất kỳ workflow nào chạy
   từ repo fork hoặc branch khác đều bị AWS STS từ chối cấp token.
2. **Hiểu đúng về Wildcard trong AWS IAM:** Ký tự đại diện `*` trong
   `Resource = ["*"]` **chỉ được chấp nhận duy nhất** cho hành động
   `ecr:GetAuthorizationToken`. Đây là đặc thù bắt buộc của AWS IAM vì service
   này không hỗ trợ phân quyền ở cấp độ tài nguyên cho token xác thực ban đầu.
   Ngược lại, mọi permission khác (`ecr:PutImage`, `apprunner:StartDeployment`)
   đều bắt buộc phải khóa chặt vào Account ID cụ thể lấy từ
   `data.aws_caller_identity.current.account_id` và tên repository cụ thể.
3. **Tên ECR Repository tuân thủ chuẩn:** Biến `ecr_repository_name` được tách
   riêng và áp dụng validation bắt buộc viết thường (`^[a-z0-9][a-z0-9-_/]*$`),
   tránh xung đột với quy tắc đặt tên viết hoa của GitHub repository.

~~~hcl
# Trích đoạn từ terraform/main.tf
data "aws_caller_identity" "current" {}

condition {
  test     = "StringEquals"
  variable = "token.actions.githubusercontent.com:sub"
  values   = ["repo:Minhlike/Golang:environment:production"]
}
~~~

Lưu ý: cấu hình Terraform này là tài liệu và mã nguồn kiểm tra cú pháp
(reviewable code). Nó không chứng minh rằng role đã assume thành công, không
chứng minh tài nguyên ECR/App Runner thực tế tồn tại, và không chứng minh lệnh
deploy đã hoàn tất. Máy hiện tại không cài `terraform` hay `aws`; ta giữ
blocker này rõ ràng, không tự cài và không tạo tài nguyên cloud thật.

@table Bảy tầng bằng chứng trong quy trình delivery có trách nhiệm

| Tầng bằng chứng | Bản chất kỹ thuật | Trách nhiệm kiểm chứng | Giới hạn không được suy diễn |
| --- | --- | --- | --- |
| Source Revision | Git commit SHA. | Git commit graph. | Chưa chứng minh code biên dịch được. |
| Verification | `go test`, `go vet`, `go test -race`. | Runner CI dependency graph. | Chỉ bao phủ các ca kiểm thử hiện có. |
| Local Image ID | Config JSON hash (`.Id`). | Docker daemon cục bộ. | Không dùng làm định danh kéo ảnh từ xa. |
| Manifest Digest | OCI Manifest Hash (`sha256:`). | Buildx metadata / Registry. | Chưa chứng minh container chạy đúng logic. |
| Provenance | Build attestation metadata. | Verifier chuyên trách (Cosign/GH). | Thiếu verifier thì không được coi là verified. |
| Promotion Gate | CLI Go kiểm tra fail-closed. | Admission policy. | Không thay thế được môi trường production thật. |
| Deployment | Cập nhật desired state cụm. | Orchestrator controller. | Replica Available không bảo đảm business SLO. |

**Dừng để dự đoán.** Nếu một pipeline CI tự động gán cờ `--provenance-verified=true`
mà không chạy bất kỳ lệnh xác thực chữ ký nào, điều gì sẽ xảy ra nếu một kẻ tấn
công thay thế image trong registry bằng một image độc hại có cùng tag? Tại sao
đây lại được gọi là "evidence theater"?

## Điểm dừng: evidence không thay thế trách nhiệm

Pipeline, OIDC, attestation, Deployment và rollback không làm software tự an toàn. Chúng làm đường đi của một thay đổi có thể kiểm tra: source nào, artifact nào, gate nào, quyền nào, rollout nào và hành động nào khi xấu. Đó là nền để một Go service có thể được phát hành nhiều lần mà không biến mỗi lần phát hành thành một niềm tin mơ hồ.

Từ đây, sách có thể quay vào case study lớn hơn: một service nhận input, chạy work có deadline, phát signal, được đóng gói, rồi được đưa qua delivery policy và phục hồi có evidence. Mỗi công cụ chỉ được thêm khi câu hỏi vận hành đã tồn tại.

@references
1. GitHub Docs. Secure use reference: least privilege, `GITHUB_TOKEN`, secret risks và OIDC. docs.github.com/en/actions/reference/security/secure-use
2. GitHub Docs. OpenID Connect: token ngắn hạn, trust relationship và cloud authorization. docs.github.com/en/actions/concepts/security/openid-connect
3. GitHub Docs. Security for GitHub Actions: artifact attestations và deployment hardening. docs.github.com/en/actions/how-tos/secure-your-work
4. Kubernetes Authors. Deployments: rollout status, revision, rollback và giới hạn của revision history. kubernetes.io/docs/concepts/workloads/controllers/deployment/
5. AWS Documentation. Creating OpenID Connect (OIDC) identity providers và IAM role trust policies. docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html
6. HashiCorp Terraform. AWS Provider: `aws_iam_openid_connect_provider` và `aws_iam_role`. registry.terraform.io/providers/hashicorp/aws/latest/docs
