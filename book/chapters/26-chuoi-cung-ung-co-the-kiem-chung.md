# Chương 26 — Chuỗi cung ứng phần mềm có thể kiểm chứng

Trong phát triển phần mềm hiện đại, ứng dụng của bạn hiếm khi được viết từ con số không. Một dịch vụ Go thông thường có thể chỉ chứa vài nghìn dòng code nghiệp vụ, nhưng lại kéo theo hàng chục thư viện bên ngoài (dependencies), hàng trăm module gián tiếp và vận hành bên trong một container image chứa hàng nghìn gói nhị phân của hệ điều hành.

Điều đó tạo nên một bề mặt tấn công khổng lồ mang tên: **Chuỗi cung ứng phần mềm (Software Supply Chain)**.

Các sự cố an ninh nghiêm trọng trên thế giới — từ SolarWinds, Codecov cho đến các cuộc tấn công Dependency Confusion và Typosquatting — đã chỉ ra một sự thật cay đắng:
> *Một kho mã nguồn sạch, được review kỹ lưỡng và vượt qua mọi bài kiểm thử unit test, vẫn có thể cho ra lò một container image độc hại nếu quy trình build, dependency hoặc kho lưu trữ artifact bị xâm phạm.*

Làm thế nào để đảm bảo rằng container image đang chuẩn bị chạy trên cụm Kubernetes của bạn:
1. Được biên dịch chính xác từ commit đã được phê duyệt trong Git?
2. Không bị tráo đổi nội dung sau khi xuất xưởng khỏi quy trình CI?
3. Không chứa các lỗ hổng bảo mật nghiêm trọng có thể kích hoạt từ xa?
4. Được bảo chứng bằng chữ ký mật mã không thể chối bỏ?

Chương này hướng dẫn bạn tư duy và xây dựng một **Cổng kiểm soát chuỗi cung ứng phần mềm (Supply Chain Verification Gate)** bằng Go theo nguyên tắc đóng kín (fail-closed), tích hợp kiểm chứng digest OCI, chữ ký số mật mã ECDSA, chứng thực nguồn gốc SLSA và phân tích khả năng vươn tới của lỗ hổng (`govulncheck`).

---

## 1. Mental Model: Chuỗi bảo chứng từ Mã nguồn đến Triển khai

Mô hình tư duy cốt lõi của một chuỗi cung ứng có thể kiểm chứng được mô tả qua quy trình 6 bước không thể phá vỡ:

~~~
[Mã nguồn Git] (Commit SHA bất biến)
      │
      ▼
[Đồ thị phụ thuộc] (go.sum + Checksum Database)
      │
      ▼
[Quy trình Build cô lập] (Tạo SLSA Provenance Attestation)
      │
      ▼
[Artifact Container] (Định danh bằng sha256 Content Digest)
      │
      ▼
[Ký số mật mã] (Cosign / Sigstore Keyless Signature)
      │
      ▼
[Cổng chính sách Fail-Closed] (Chặn đứng mọi sai lệch)
      │
      ▼
[Quyết định Triển khai] (ALLOW hoặc DENY)
~~~

Trong mô hình này, mỗi mắt xích phía sau đều đòi hỏi bằng chứng toán học hoặc mật mã học để chứng minh tính hợp lệ của mắt xích phía trước. Tệp `go.sum` bảo chứng tính toàn vẹn của mã nguồn bên thứ ba khi tải về máy chủ phát triển. Bản chứng thực SLSA Provenance xác nhận chính xác hạ tầng và quy trình build nào đã tạo ra tệp nhị phân. Mã băm OCI Digest bảo đảm nội dung container image không bị sai lệch dù chỉ một bit. Cùng với đó, chữ ký mật mã Cosign xác nhận danh tính của thực thể phát hành, cho phép cổng chính sách (Policy Engine) hoạt động như một chốt chặn đóng kín (fail-closed) với nguyên tắc mặc định từ chối (deny by default) trừ khi mọi bằng chứng đều được kiểm chứng trọn vẹn.

---

## 2. Toàn vẹn Module: `go.sum` và Go Checksum Database

Trước khi container image được build, chuỗi cung ứng bắt đầu ngay tại thời điểm Go tải các gói phụ thuộc về máy.

### Bản chất kỹ thuật của `go.sum`

Một ngộ nhận kinh điển trong cộng đồng là coi `go.sum` như một tệp khóa phiên bản tương tự `package-lock.json` hay `yarn.lock`. Về mặt bản chất, tệp `go.mod` mới là nơi quyết định phiên bản module thông qua giải thuật lựa chọn phiên bản tối thiểu (Minimal Version Selection - MVS). Ngược lại, `go.sum` là cơ sở dữ liệu xác thực nội dung mật mã (Content Validation Database). Nó lưu trữ các mã băm SHA-256 của toàn bộ mã nguồn module và tệp `go.mod` tương ứng nhằm phát hiện mọi hành vi can thiệp trái phép hoặc thay đổi nội dung sau thời điểm phát hành chính thức.

Mỗi bản ghi trong `go.sum` được cấu trúc thành hai dòng thông tin bổ trợ:

~~~
github.com/gin-gonic/gin v1.9.1 h1:4A06lVSJ...
github.com/gin-gonic/gin v1.9.1/go.mod h1:h1hp...
~~~

Dòng định dạng `h1:<base64-hash>` chứa chuỗi băm SHA-256 được tính toán trên toàn bộ cây thư mục mã nguồn sau khi giải nén. Dòng có hậu tố `/go.mod` lưu trữ mã băm chỉ tính riêng trên nội dung tệp khai báo phụ thuộc của module đó, cho phép công cụ Go kiểm tra cây phụ thuộc một cách nhanh chóng mà không bắt buộc phải tải toàn bộ mã nguồn của các module gián tiếp về máy.

### Go Checksum Database (`sum.golang.org`)
Nếu một kẻ xấu xâm nhập được máy chủ Git của một thư viện bên thứ ba và tráo đổi nội dung của release tag `v1.2.0`, điều gì sẽ xảy ra?

Nếu máy bạn chưa từng tải bản release đó, làm sao Go biết mã băm `h1:` nào là chuẩn?

Go giải quyết triệt để vấn đề này thông qua **Go Checksum Database (sum.golang.org)** — một sổ cái minh bạch (Transparency Log) dựa trên cấu trúc cây Merkle:
1. Khi máy của bạn tải một module mới lần đầu tiên, Go toolchain sẽ truy vấn `sum.golang.org`.
2. Checksum Database chỉ ghi nhận mã băm của một module một lần duy nhất (nhật ký append-only).
3. Nếu hacker thay đổi code của tag `v1.2.0`, mã băm tải về sẽ không khớp với bản ghi trong sổ cái toàn cầu. Go sẽ lập tức hủy bỏ quá trình build với thông báo lỗi:
   `SECURITY ERROR: checksum mismatch`.

> [!IMPORTANT]
> **Quy tắc vàng:** Tệp `go.sum` BẮT BUỘC phải được commit vào Git repository. Tuyệt đối không đưa `go.sum` vào `.gitignore`. Bỏ qua `go.sum` đồng nghĩa với việc mở toang cửa cho các cuộc tấn công tráo đổi mã nguồn phụ thuộc.

---

## 3. Quét lỗ hổng tĩnh vs Khả năng vươn tới ký hiệu (`govulncheck`)

Trong các pipeline CI/CD truyền thống, các công cụ quét container (như Trivy, Grype, Snyk) thường đối chiếu danh sách gói phần mềm với cơ sở dữ liệu CVE. Cách tiếp cận này tạo ra một vấn nạn nghiêm trọng trong vận hành: **Hội chứng mệt mỏi vì cảnh báo (Alert Fatigue)**.

Một dự án Go có thể sử dụng thư viện `golang.org/x/crypto`. Giả sử thư viện này có một lỗ hổng nghiêm trọng trong hàm xử lý khóa SSH: `ssh.ParsePrivateKey`. Máy quét tĩnh truyền thống chỉ nhìn vào sự xuất hiện của `golang.org/x/crypto` trong `go.mod` và lập tức kích hoạt cảnh báo chặn đứng pipeline phát hành, dù trên thực tế ứng dụng của bạn chỉ gọi hàm `bcrypt.GenerateFromPassword` để băm mật khẩu và hoàn toàn không bao giờ chạm tới module SSH.

### Cơ chế phân tích đồ thị cuộc gọi của `govulncheck`
Công cụ chính thức của Go team — `govulncheck` — hoạt động theo một nguyên lý hoàn toàn khác biệt: **Phân tích khả năng vươn tới của ký hiệu (Symbol Reachability Analysis)**.

~~~
[Ứng dụng: main.go]
      │
      ├──> bcrypt.GenerateFromPassword (Được gọi)
      │
      └──X (Bỏ qua) ssh.ParsePrivateKey [CRITICAL]
~~~

Bản chất dữ liệu đầu ra của `govulncheck`:
1. Đầu ra JSON có cấu trúc của `govulncheck` chứa các bản ghi: **`OSV`** (thông tin lỗ hổng định dạng Open Source Vulnerability), **`Modules`** (danh sách module liên quan), và **`Traces`** (đồ thị dấu vết cuộc gọi từ `main` tới ký hiệu bị tổn thương).
2. `govulncheck` **không** tự sinh ra trường nguyên thủy `Severity: "CRITICAL"` trong output thô; mức độ nghiêm trọng (Severity) được làm giàu từ cơ sở dữ liệu OSV hoặc CVSS bên ngoài.
3. Thuộc tính `Reachable: true` trong mô hình chính sách là kết quả tổng hợp sau khi duyệt qua mảng `Traces`: nếu tồn tại ít nhất một đường dẫn hợp lệ từ `main` tới hàm chứa lỗi, lỗ hổng được xác định là thực sự có thể kích hoạt (`Reachable`).

### Giới hạn phân tích cần lưu ý

Cần lưu ý rằng khả năng phân tích tĩnh của `govulncheck` tập trung hoàn toàn vào mã nguồn Go thuần túy. Công cụ không phân tích các phụ thuộc liên kết động qua CGO runtime, không tự động lần vết mã độc trong các plugin tải động tại thời điểm chạy (`plugin.Open`), và không quét các thư viện hệ thống nhị phân trong base image container (như OpenSSL hay glibc — những thành phần này vẫn cần các công cụ quét container chuyên dụng bổ trợ).

### Thiết kế chính sách thông minh

Từ góc độ cổng kiểm soát chính sách (Gate Policy), hệ thống chia tách hành vi dựa trên kết quả phân tích khả năng vươn tới. Khi một lỗ hổng nghiêm trọng được xác định nằm trực tiếp trên đường thực thi của ứng dụng (`Reachable = true`), cổng lập tức ra quyết định từ chối triển khai (`DENY`). Ngược lại, nếu một thư viện phụ thuộc chứa lỗ hổng nhưng hàm bị tổn thương hoàn toàn không bao giờ được mã nguồn gọi tới (`Reachable = false`), hệ thống ghi nhận cảnh báo kiểm toán (`WARN`) để đội ngũ kỹ sư lên kế hoạch nâng cấp mà không làm đứt gãy tiến độ phát hành sản phẩm.

---

## 4. Bất biến OCI: Mã băm Digest vs Nhãn Tag có thể biến đổi

Khi container image được đóng gói và đẩy lên OCI Registry (Docker Hub, AWS ECR, GitHub Packages), chúng ta thường gắn thẻ tag như `:latest` hoặc `:v1.2.3`.

Tuy nhiên, trong thế giới container:
> **Tag là con trỏ có thể thay đổi (Mutable Pointer), chỉ có Digest mới là Nguồn chân lý bất biến (Immutable Truth).**

~~~
Tag:    my-app:v1.2.0 (Con trỏ có thể bị ghi đè)
             │
             ▼
Digest: sha256:7f83b1657ff1... (Mã băm bất biến)
        (Định danh duy nhất theo nội dung)
~~~

Nếu bạn cấu hình Kubernetes Deployment dùng `image: my-app:v1.2.0`, kẻ tấn công có quyền ghi vào registry có thể đẩy một image độc hại đè lên tag này. Khi Pod khởi động lại hoặc mở rộng quy mô trên máy chủ mới, kubelet sẽ tự động tải image độc hại về thực thi mà hệ thống kiểm soát không nhận diện được bất kỳ sự thay đổi cấu hình nào.

Vì vậy, Cổng kiểm soát chuỗi cung ứng chuẩn mực luôn thực thi quy tắc đầu tiên:
**Từ chối mọi image không được định danh tường minh bằng mã băm SHA-256 dạng `sha256:<64_hex_chars>`.**

---

## 5. Chữ ký số Sigstore/Cosign và Attestation SLSA

Làm sao chúng ta biết một container image có mã băm `sha256:abc...` thực sự được tạo ra bởi quy trình CI chính thức của tổ chức chứ không phải do hacker tự biên dịch rồi đẩy lên?

Giải pháp hiện đại nhất là hệ sinh thái **Sigstore / Cosign**:
1. **Ký không cần khóa (Keyless Signing):** Không còn nỗi lo lưu trữ private key dài hạn trên máy chủ CI (vốn rất dễ bị rò rỉ). CI Runner sử dụng OpenID Connect (OIDC) token do GitHub Actions cấp phát để chứng minh danh tính với nhà cấp phát chứng chỉ Sigstore (Fulcio).
2. **Chứng chỉ ngắn hạn:** Fulcio cấp chứng chỉ X.509 có hiệu lực trong vài phút, gắn liền với danh tính workflow (`https://token.actions.githubusercontent.com`).
3. **Ký trên Digest:** Chữ ký số (ECDSA P-256) được tính toán trực tiếp trên mã băm OCI Digest của image.
4. **SLSA Provenance Attestation:** Ngoài chữ ký, CI còn tạo ra bản chứng thực nguồn gốc (Provenance) ghi rõ: Commit SHA nào, quy trình workflow nào (Builder ID) đã tạo ra artifact.

---

## 6. Xây dựng Cổng chính sách Fail-Closed trong Go

Bây giờ, chúng ta sẽ hiện thực hóa toàn bộ các nguyên lý trên vào một module Go theo **Mô hình chính sách kiểm chứng sư phạm (Pedagogical Verification Policy Model)**. 

Mô hình này không nhằm mục đích thay thế hay bao bọc toàn bộ mã nguồn của Cosign CLI hay SLSA verifier bên ngoài. Thay vào đó, nó tách bạch rõ ràng 3 khế ước giao tiếp (interfaces) cốt lõi của một hệ thống kiểm định chuỗi cung ứng hiện đại:
1. `SignatureVerifier`: Chịu trách nhiệm xác thực chữ ký số mật mã của image (Cosign / Notary).
2. `ProvenanceVerifier`: Chịu trách nhiệm kiểm chứng xuất xứ bản build (SLSA Provenance / in-toto).
3. `VulnerabilityProvider`: Chịu trách nhiệm cung cấp dữ liệu lỗ hổng (govulncheck / scanner).

### Khai báo các Interface và Mô hình dữ liệu chính sách

~~~go
type Decision string

const (
	DecisionAllow Decision = "ALLOW"
	DecisionDeny  Decision = "DENY"
)

// 3 Interface cốt lõi của Cổng kiểm định chuỗi cung ứng:
type SignatureVerifier interface {
	VerifySignature(
		digest string, sig *SignatureVerification,
	) error
}

type ProvenanceVerifier interface {
	VerifyProvenance(
		digest string, att *Attestation,
	) error
}

type VulnerabilityProvider interface {
	GetVulnerabilities(
		digest string,
	) ([]Vulnerability, error)
}

// Vulnerability mô phỏng phát hiện với ngữ nghĩa
// reachability của govulncheck và mức độ từ OSV.
type Vulnerability struct {
	ID        string `json:"id"`
	Package   string `json:"package"`
	Symbol    string `json:"symbol"`
	Severity  string `json:"severity"` // Từ OSV
	Reachable bool   `json:"reachable"` // Từ call-graph
}
~~~

### Metadata Xuất xứ, Chữ ký số và Bộ điều phối PolicyEngine

~~~go
// Attestation đại diện cho metadata xuất xứ SLSA.
type Attestation struct {
	BuilderID     string `json:"builderId"`
	SubjectDigest string `json:"subjectDigest"`
}

// SignatureVerification chứa thông tin chữ ký ECDSA
// và định danh OIDC Issuer.
type SignatureVerification struct {
	PublicKey *ecdsa.PublicKey
	Signature []byte
	Issuer    string
}

type EvaluationResult struct {
	Decision   Decision `json:"decision"`
	Violations []string `json:"violations,omitempty"`
	Warnings   []string `json:"warnings,omitempty"`
}

// PolicyEngine điều phối việc kiểm định fail-closed
type PolicyEngine struct {
	TrustedBuilders []string
	TrustedIssuers  []string
	SigVerifier     SignatureVerifier
	ProvVerifier    ProvenanceVerifier
}

func NewPolicyEngine(builders, issuers []string) *PolicyEngine {
	sigV := &DefaultSignatureVerifier{
		TrustedIssuers: issuers,
	}
	provV := &DefaultProvenanceVerifier{
		TrustedBuilders: builders,
	}
	return &PolicyEngine{
		TrustedBuilders: builders,
		TrustedIssuers:  issuers,
		SigVerifier:     sigV,
		ProvVerifier:    provV,
	}
}
~~~

### Kiểm tra tính bất biến của OCI Digest

~~~go
// VerifyDigest xác thực artifact dùng mã băm bất biến.
func VerifyDigest(digest string) error {
	if !digestRegex.MatchString(digest) {
		return errors.New(
			"invalid OCI digest: must be sha256:64hex",
		)
	}
	return nil
}
~~~

### Xác thực chữ ký mật mã ECDSA và OIDC Issuer

~~~go
func (e *PolicyEngine) VerifySignature(
	digest string,
	sig *SignatureVerification,
) error {
	if sig == nil || sig.PublicKey == nil {
		return errors.New(
			"missing cryptographic signature or public key",
		)
	}

	// 1. Kiểm tra OIDC Issuer có nằm trong danh sách tin cậy
	trustedIssuer := false
	for _, ti := range e.TrustedIssuers {
		if sig.Issuer == ti {
			trustedIssuer = true
			break
		}
	}
	if !trustedIssuer {
		return fmt.Errorf(
			"untrusted OIDC signature issuer: %s",
			sig.Issuer,
		)
	}

	// 2. Kiểm tra chữ ký toán học ECDSA P-256
	hash := sha256.Sum256([]byte(digest))
	if len(sig.Signature) == 0 {
		return errors.New("empty signature payload")
	}

	valid := ecdsa.VerifyASN1(
		sig.PublicKey, hash[:], sig.Signature,
	)
	if !valid {
		return errors.New(
			"signature verification failed: bad signature",
		)
	}
	return nil
}
~~~

### Thực thi đánh giá toàn diện (Fail-Closed Evaluation)

Khâu thẩm định được chia thành các chốt chặn nối tiếp nhau. Đầu tiên là kiểm tra tính toàn vẹn của mã băm và chữ ký số:

~~~go
func (e *PolicyEngine) evaluateIntegrity(
	digest string,
	sig *SignatureVerification,
	res *EvaluationResult,
) bool {
	// Cửa 1: Khóa cứng tính bất biến OCI Digest
	if err := VerifyDigest(digest); err != nil {
		res.Decision = DecisionDeny
		res.Violations = append(res.Violations, err.Error())
		return false // Dừng ngay lập tức (fail closed)
	}

	// Cửa 2: Xác thực chữ ký số Cosign
	if err := e.VerifySignature(digest, sig); err != nil {
		res.Decision = DecisionDeny
		res.Violations = append(res.Violations, err.Error())
	}
	return true
}
~~~

Tiếp theo là chốt chặn kiểm chứng xuất xứ bản build (SLSA Provenance) để bảo đảm artifact không bị đánh tráo từ một pipeline lạ:

~~~go
func (e *PolicyEngine) evaluateProvenance(
	digest string,
	att *Attestation,
	res *EvaluationResult,
) {
	// Cửa 3: Kiểm chứng xuất xứ SLSA và Builder ID
	if att == nil {
		res.Decision = DecisionDeny
		res.Violations = append(
			res.Violations,
			"missing SLSA provenance attestation",
		)
		return
	}

	if att.SubjectDigest != digest {
		res.Decision = DecisionDeny
		res.Violations = append(
			res.Violations,
			"provenance subject digest mismatch",
		)
	}

	builderOK := false
	for _, tb := range e.TrustedBuilders {
		if att.BuilderID == tb {
			builderOK = true
			break
		}
	}
	if !builderOK {
		res.Decision = DecisionDeny
		res.Violations = append(
			res.Violations,
			fmt.Sprintf(
				"untrusted builder: %s",
				att.BuilderID,
			),
		)
	}
}
~~~

Cuối cùng là chốt chặn kiểm tra lỗ hổng bảo mật với ngữ nghĩa reachability của `govulncheck`:

~~~go
func (e *PolicyEngine) evaluateVulnerabilities(
	vulns []Vulnerability,
	res *EvaluationResult,
) {
	// Cửa 4: Kiểm soát lỗ hổng govulncheck
	for _, v := range vulns {
		isCrit := strings.EqualFold(v.Severity, "CRITICAL")
		isHigh := strings.EqualFold(v.Severity, "HIGH")

		if isCrit || isHigh {
			if v.Reachable {
				// Hàm lỗi trên đường thực thi: TỪ CHỐI
				res.Decision = DecisionDeny
				res.Violations = append(
					res.Violations,
					fmt.Sprintf(
						"reachable %s vuln %s (sym: %s)",
						v.Severity, v.ID, v.Symbol,
					),
				)
			} else {
				// Hàm lỗi không được gọi: CẢNH BÁO
				res.Warnings = append(
					res.Warnings,
					fmt.Sprintf(
						"uncalled %s vuln %s: tolerated",
						v.Severity, v.ID,
					),
				)
			}
		}
	}
}
~~~

Hàm `Evaluate` chính thức chỉ việc điều phối tuần tự 3 chốt chặn:

~~~go
func (e *PolicyEngine) Evaluate(
	digest string,
	sig *SignatureVerification,
	att *Attestation,
	vulns []Vulnerability,
) EvaluationResult {
	res := EvaluationResult{Decision: DecisionAllow}
	if !e.evaluateIntegrity(digest, sig, &res) {
		return res
	}
	e.evaluateProvenance(digest, att, &res)
	e.evaluateVulnerabilities(vulns, &res)
	return res
}
~~~

---

## 7. Kiểm chứng Lab thực tế (`labs/part26-supply-chain-gate`)

Mã nguồn hoàn chỉnh của bài lab nằm tại thư mục `labs/part26-supply-chain-gate` (phân loại mức kiểm chứng: `UNIT_TESTED` / `MODEL_ONLY` đối với logic chính sách cổng fail-closed và chữ ký ECDSA P-256 nội bộ, chứng minh khế ước an ninh của 5 kịch bản thực chiến mà không phụ thuộc vào hạ tầng mạng Sigstore bên ngoài). Khi chạy kiểm thử với cờ kiểm tra xung đột dữ liệu:

~~~bash
go test -v -race ./...
~~~

Bộ kiểm thử thực hiện xác minh 5 kịch bản thực chiến:

~~~
=== RUN   TestPolicyGateAllowedWithValidSignature
--- PASS: TestPolicyGateAllowedWithValidSignature (0.00s)
=== RUN   TestPolicyGateDenyUnsignedImage
--- PASS: TestPolicyGateDenyUnsignedImage (0.00s)
=== RUN   TestPolicyGateDenyReachableVulnerability
--- PASS: TestPolicyGateDenyReachableVulnerability (0.00s)
=== RUN   TestPolicyGateAllowUncalledVulnerability
--- PASS: TestPolicyGateAllowUncalledVulnerability (0.00s)
=== RUN   TestPolicyGateFailClosedOnMutableTag
--- PASS: TestPolicyGateFailClosedOnMutableTag (0.00s)
PASS
ok      part26-supply-chain-gate   2.128s
~~~

### Phân tích các kịch bản kiểm thử:
1. **Artifact hợp lệ toàn diện:** Có chữ ký ECDSA hợp lệ, ký bởi GitHub Actions OIDC, provenance khớp digest và không có CVE $\rightarrow$ **`ALLOW`**.
2. **Image không có chữ ký:** Bị chặn đứng ngay tại Cửa 2 $\rightarrow$ **`DENY`**.
3. **Lỗ hổng nghiêm trọng có thể vươn tới (`Reachable = true`):** Ký hiệu `ssh.ParsePrivateKey` được gọi trong ứng dụng $\rightarrow$ **`DENY`**.
4. **Lỗ hổng nằm trong dependency nhưng không được gọi (`Reachable = false`):** Ký hiệu `http2.Server.ServeConn` không nằm trong luồng thực thi $\rightarrow$ **`ALLOW`** kèm thông điệp cảnh báo kiểm toán trong danh sách `Warnings`.
5. **Cố tình dùng tag thay vì digest:** Truyền vào chuỗi `my-registry.io/app:v1.2.0` $\rightarrow$ Bị chặn ngay từ Cửa 1 $\rightarrow$ **`DENY`**.

---

## 8. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **Triển khai bằng Docker tag** (`:latest` hoặc `:v1.0.0`) thay vì sha256 digest. | Bị tấn công tráo đổi container image khi registry bị thỏa hiệp; pod scale up chạy phiên bản khác nhau. | Bắt buộc ghim (pin) mã băm bất biến `sha256:<hex>` trong Kubernetes Pod Spec. |
| **Chỉ kiểm tra chữ ký hợp lệ** mà không kiểm tra danh tính người ký (OIDC Issuer). | Kẻ tấn công tự tạo cặp khóa ECDSA riêng rồi tự ký image của chúng, cổng vẫn cho qua. | Luôn đối chiếu `sig.Issuer` và `att.BuilderID` với danh sách trắng (Trusted Anchors). |
| **Thiết kế Cổng dạng Fail-Open:** Bỏ qua kiểm tra khi mạng tới OIDC/Registry bị timeout. | Khi mạng gặp sự cố, hệ thống tự động cho phép mọi image chưa được kiểm chứng đi thẳng vào production. | Luôn áp dụng nguyên tắc Fail-Closed: Bất kỳ lỗi mạng hay timeout nào cũng phải quy về `DENY`. |
| **Đưa `go.sum` vào `.gitignore`** vì cho rằng tệp này tự sinh và gây phiền phức khi merge code. | Mất đi chốt chặn xác minh tính toàn vẹn của thư viện bên thứ ba; dễ bị tấn công MITM. | Luôn commit `go.sum` vào Git; chạy `go mod verify` trong mọi pipeline CI. |

---

## 9. Bài tập thực hành thiết kế Cổng bảo vệ

### Thử thách 1: Ghim Base Image chuẩn (Golden Image Pinning)
**Yêu cầu:** Trong tệp Dockerfile nhiều tầng (multi-stage build), tầng thực thi cuối cùng thường bắt đầu bằng một base image (ví dụ `gcr.io/distroless/static-debian12`). Hãy viết một hàm Go nhận vào danh sách base images tin cậy (dưới dạng ánh xạ giữa tên image và mã băm sha256 cho phép) và kiểm tra xem một dòng `FROM <image>` trong Dockerfile có tuân thủ đúng mã băm đã được phê duyệt hay không.

### Thử thách 2: Cơ chế Timeout Fail-Closed (Network Timeout Fallback)
**Yêu cầu:** Khi cổng kiểm tra gọi sang máy chủ Rekor hoặc Fulcio qua mạng, nếu request bị timeout (quá 2 giây), hãy thiết kế một cấu trúc hàm sao cho: thay vì trả về lỗi chung chung khiến người vận hành bối rối, hàm phải trả về quyết định `DENY` kèm thông điệp vi phạm giải thích rõ ràng rằng: Cổng đã chủ động đóng lại theo nguyên tắc Fail-Closed để bảo vệ an toàn cho cụm máy chủ.

---

## 10. Hướng dẫn giải và Phân tích kiến trúc bài tập

### Lời giải Thử thách 1: Xác thực Golden Base Image

~~~go
type GoldenCatalog map[string]string

func VerifyBaseImage(
	imageRef string,
	catalog GoldenCatalog,
) (bool, error) {
	parts := strings.Split(imageRef, "@")
	if len(parts) != 2 {
		return false, fmt.Errorf(
			"image must be pinned with digest: repo@sha256:hex",
		)
	}

	repo := parts[0]
	digest := parts[1]

	expectedDigest, exists := catalog[repo]
	if !exists {
		return false, fmt.Errorf(
			"untrusted base image repository: %s", repo,
		)
	}

	if digest != expectedDigest {
		return false, fmt.Errorf(
			"base image digest mismatch: expected %s, got %s",
			expectedDigest, digest,
		)
	}

	return true, nil
}
~~~

### Lời giải Thử thách 2: Xử lý Timeout theo nguyên tắc Fail-Closed

~~~go
func SafeRemoteVerify(
	ctx context.Context,
	verifyFunc func(context.Context) error,
) EvaluationResult {
	// Giới hạn thời gian xác thực tối đa 2 giây
	timeoutCtx, cancel := context.WithTimeout(
		ctx, 2*time.Second,
	)
	defer cancel()

	err := verifyFunc(timeoutCtx)
	if err != nil {
		// Nguyên tắc Fail-Closed: Bất kỳ sự cố mạng nào
		// cũng dẫn đến quyết định TỪ CHỐI (DENY)
		return EvaluationResult{
			Decision: DecisionDeny,
			Violations: []string{
				fmt.Sprintf("fail-closed: aborted: %v", err),
			},
		}
	}

	return EvaluationResult{Decision: DecisionAllow}
}
~~~

Nhờ cơ chế Fail-Closed, ngay cả khi nhà cung cấp dịch vụ xác thực gặp sự cố ngừng hoạt động (outage), hệ thống của bạn vẫn được bảo vệ tuyệt đối trước nguy cơ lọt lưới các artifact độc hại.

---

Sau khi đã làm chủ quy trình kiểm soát chuỗi cung ứng phần mềm — từ tính toàn vẹn của mã nguồn, xuất xứ build đến chữ ký số artifact container — chúng ta đã có thể yên tâm rằng các file nhị phân chạy trên production là nguyên bản và an toàn. 

Nhưng khi các container đó thực sự chạy trên hệ điều hành, làm thế nào để bạn biết chắc chúng đang làm gì dưới tầng nhân (kernel)? Liệu có tiến trình lạ nào đang bí mật mở kết nối mạng, đọc trộm tệp tin cấu hình hay cố gắng leo thang đặc quyền mà các công cụ giám sát thông thường không nhìn thấy? Trong **Chương 27**, chúng ta sẽ thâm nhập vào tầng sâu nhất của hệ điều hành Linux: sử dụng **eBPF (Extended Berkeley Packet Filter) kết hợp với Go** để quan sát và bắt trọn từng hành vi của hệ thống trực tiếp từ kernel mà không làm chậm ứng dụng.
