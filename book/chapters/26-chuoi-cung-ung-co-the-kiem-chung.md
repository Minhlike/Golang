<!-- BOOK_ROLE: APPLICATION_SYSTEMS -->

# Chương 26 — Chuỗi cung ứng phần mềm có thể kiểm chứng

Một kịch bản chuỗi cung ứng phần mềm điển hình có thể bao gồm mã nguồn nghiệp vụ, nhiều module phụ thuộc gián tiếp và ảnh nền container (base image) chứa sẵn các gói cài đặt của hệ điều hành. Số lượng thành phần thực tế phụ thuộc vào phương thức đóng gói: một ảnh nền tối giản `scratch` và một ảnh nền hệ điều hành đầy đủ có tập hợp gói phần mềm hoàn toàn khác nhau. Vì vậy danh mục thành phần (inventory) phải được kết xuất trực tiếp từ artifact thực tế, không thể ước lượng cảm tính từ số dòng mã nguồn Go của ứng dụng.

Thực tế này mở rộng bề mặt rủi ro của chuỗi cung ứng phần mềm (software supply chain).

Các sự cố an ninh thực tế như SolarWinds, Codecov hay các cuộc tấn công nhầm lẫn phụ thuộc (dependency confusion) và giả mạo định danh gói (typosquatting) chứng minh một ranh giới bảo mật quan trọng:
> *Một kho mã nguồn sạch, được duyệt kỹ lưỡng và vượt qua mọi bài kiểm thử đơn vị, vẫn có thể tạo ra một container image độc hại nếu quy trình đóng gói, gói phụ thuộc hoặc kho lưu trữ artifact bị xâm phạm.*

Ta cần kiểm tra ảnh container nào đã được xét, bằng chứng nào gắn nó với bộ dựng hoặc nguồn mã được phép, và phát hiện lỗ hổng nào phải chặn theo chính sách kiểm soát. Chữ ký và việc quét mã không chứng minh gói phát hành hoàn toàn sạch mã độc hay lỗ hổng; từng bộ kiểm chứng chỉ đưa ra kết luận trong phạm vi dữ liệu và gốc tin cậy của nó.

Chương này hướng dẫn xây dựng cổng kiểm soát chuỗi cung ứng phần mềm bằng Go theo nguyên tắc đóng an toàn (*fail-closed*, tức từ chối mặc định khi thiếu chứng cứ), tích hợp kiểm chứng mã băm nội dung (*digest*) OCI, chữ ký số mật mã ECDSA, chứng thực nguồn gốc SLSA và phân tích khả năng vươn tới của lỗ hổng (`govulncheck`).

---

## 1. Mental Model: Chuỗi bảo chứng từ Mã nguồn đến Triển khai

Mô hình dưới đây nối sáu chặng của một policy delivery. Mỗi mũi tên đòi bằng chứng riêng; đây không phải chuỗi tự bảo chứng:

![Chuỗi bằng chứng và cổng chính sách triển khai](../../assets/diagrams/supply-chain-policy-evidence.png)
@figure Cổng chỉ xác minh các bằng chứng mà chính sách yêu cầu. Mã băm nội dung, chữ ký và dữ liệu xuất xứ có vai trò khác nhau; đủ bằng chứng theo chính sách không chứng minh gói phát hành sạch mọi lỗi hoặc lỗ hổng.

Mỗi mắt xích cần bằng chứng phù hợp, nhưng không một tệp hay nhãn nào tự chứng minh toàn bộ chuỗi. `go.sum` ghi mã băm kiểm tra (*checksum*) module mà bộ công cụ biên dịch đã biết và kiểm tra, chứ không khóa hoàn toàn đồ thị như tệp khóa phiên bản. Dữ liệu xuất xứ (*provenance*) chỉ hữu ích sau khi bộ kiểm chứng xác minh đối tượng, danh tính và kỳ vọng của chính sách. Mã băm nhận diện nội dung; cơ chế xác minh không khóa (*keyless verification*) của Cosign còn kiểm tra gốc tin cậy, định danh chứng chỉ và khẳng định mã băm. Bài lab dưới đây mô hình hóa chính sách đóng an toàn, không thực hiện các bước Cosign hoặc SLSA hoàn chỉnh đó.

---

## 2. Toàn vẹn Module: `go.sum` và Go Checksum Database

Trước khi ảnh container (`container image`) được đóng gói, chuỗi cung ứng bắt đầu ngay tại thời điểm Go tải các gói phụ thuộc về máy.

### Bản chất kỹ thuật của `go.sum`

Một ngộ nhận kinh điển trong cộng đồng là coi `go.sum` như một tệp khóa phiên bản tương tự `package-lock.json` hay `yarn.lock`. Theo thiết kế, tệp `go.mod` mới là nơi quyết định phiên bản mô-đun thông qua giải thuật lựa chọn phiên bản tối thiểu (Minimal Version Selection - MVS). Ngược lại, `go.sum` là cơ sở dữ liệu xác thực nội dung mật mã (Content Validation Database). Nó lưu trữ các mã băm SHA-256 của toàn bộ mã nguồn mô-đun và tệp `go.mod` tương ứng nhằm phát hiện mọi hành vi can thiệp trái phép hoặc thay đổi nội dung sau thời điểm phát hành chính thức.

Mỗi bản ghi trong `go.sum` được cấu trúc thành hai dòng thông tin bổ trợ:

~~~
github.com/gin-gonic/gin v1.9.1 h1:4A06lVSJ...
github.com/gin-gonic/gin v1.9.1/go.mod h1:h1hp...
~~~

Dòng định dạng `h1:<base64-hash>` chứa chuỗi băm chuẩn tắc của cây thư mục mô-đun (theo giải thuật `dirhash.Hash1`): danh sách đường dẫn tệp được sắp xếp thứ tự, băm SHA-256 từng tệp, ghép thành danh sách định dạng chuẩn tắc rồi băm SHA-256 tổng thể và mã hóa base64. Dòng có hậu tố `/go.mod` lưu trữ mã băm chỉ tính riêng trên nội dung tệp khai báo phụ thuộc của mô-đun đó, cho phép công cụ Go kiểm tra cây phụ thuộc một cách nhanh chóng mà không bắt buộc phải tải toàn bộ mã nguồn của các mô-đun gián tiếp về máy.

### Go Checksum Database (`sum.golang.org`)
Nếu một kẻ xấu xâm nhập được máy chủ Git của một thư viện bên thứ ba và tráo đổi nội dung của release tag `v1.2.0`, điều gì sẽ xảy ra?

Nếu máy bạn chưa từng tải bản release đó, làm sao Go biết mã băm `h1:` nào là chuẩn?

Với các mô-đun thuộc phạm vi kiểm tra của cơ sở dữ liệu mã băm và cấu hình mặc định phù hợp, bộ công cụ Go sẽ đối chiếu mã băm đã tải về với nhật ký minh bạch (*transparency log*) tại `sum.golang.org`. Nếu nội dung không trùng khớp, quá trình biên dịch sẽ lập tức báo lỗi kiểm tra mã băm. Cơ chế này bảo đảm tính toàn vẹn và nhất quán của nội dung tải về, hoàn toàn không chứng minh nội dung đó không chứa mã độc; các cấu hình như `GOPRIVATE`, `GONOSUMDB`, `GOSUMDB=off` và việc thay thế mã nguồn bằng chỉ thị `replace` sẽ tạo ra các ranh giới kiểm soát khác. Kỹ sư bắt buộc phải kiểm tra cấu hình biên dịch trước khi đưa ra kết luận rằng mô-đun đã đi qua cùng một quy trình thẩm định.

> Khuyến nghị: Luôn lưu trữ tệp `go.sum` cùng tệp `go.mod` vào hệ thống quản lý mã nguồn khi mô-đun có các gói phụ thuộc sinh ra tệp này. Tuyệt đối không xóa bỏ các mã băm đã được ghi nhận chỉ để tránh xung đột khi hợp nhất mã nguồn (*merge conflict*). Cơ sở dữ liệu mã băm vẫn có thể kiểm tra các mô-đun đủ điều kiện ngay cả khi chưa có mục ghi nhận cục bộ; do đó việc thiếu tệp `go.sum` không tự chứng minh rằng mã nguồn đã bị tráo đổi, nhưng sẽ làm mất đi bằng chứng mã băm độc lập mà dự án đã lưu giữ.

---

## 3. Quét lỗ hổng tĩnh vs Khả năng vươn tới ký hiệu (`govulncheck`)

Trong các đường ống tích hợp và triển khai liên tục (CI/CD) truyền thống, các công cụ quét vùng chứa (như Trivy, Grype, Snyk) thường đối chiếu danh sách gói phần mềm với cơ sở dữ liệu CVE. Cách tiếp cận này tạo ra một vấn nạn nghiêm trọng trong vận hành: hội chứng quá tải vì cảnh báo an ninh (*alert fatigue*).

Xét một tình huống: dự án dùng `golang.org/x/crypto`, và phiên bản đang dùng có cảnh báo lỗ hổng ở `ssh.ParsePrivateKey`, nhưng mã nguồn ứng dụng chỉ gọi `bcrypt.GenerateFromPassword`. Một công cụ quét chỉ nhìn danh mục gói phụ thuộc có thể báo lỗ hổng dù ký hiệu hàm không hề nằm trong đường dẫn gọi đã phân tích. Cảnh báo lỗ hổng và chặn phát hành là hai quyết định khác nhau; chính sách của đường ống CI/CD mới là nơi chọn điều kiện chặn. Đây không phải một CVE thật được gán cho phiên bản tùy ý.

### Cơ chế phân tích đồ thị cuộc gọi của `govulncheck`
Ở chế độ mã nguồn (`source`), `govulncheck` còn phân tích khả năng vươn tới của ký hiệu, thay vì chỉ báo mô-đun có lỗ hổng. Phải đọc chế độ scan và coverage của kết quả đang dùng.

![Phân biệt phụ thuộc có symbol và đường gọi có thể tới](../../assets/diagrams/vulnerability-call-reachability.png)
@figure Trong ví dụ phân tích này, ứng dụng có đường gọi tới bcrypt nhưng không thấy đường gọi tới ssh.ParsePrivateKey. Kết quả phải được hiểu trong giới hạn của bộ phân tích và build đang xét.

Dữ liệu JSON của `govulncheck` là một luồng thông điệp (*stream message*) tuân theo lược đồ (*schema*) của phiên bản sử dụng, chứa định danh OSV và phát hiện lỗ hổng kèm vết gọi (*trace*); không phải một đối tượng cố định chứa `Modules` và `Traces` viết hoa. Trong bài thực hành, `Severity` và `Reachable` là dữ liệu mẫu (*fixture*) đã được chuẩn hóa, không phải bóc tách trực tiếp từ đầu ra công cụ quét. Một phát hiện có vết gọi tới ký hiệu hàm chỉ là kết quả phân tích tĩnh về đường gọi có khả năng chạm tới, không chứng minh đường dẫn đó chắc chắn được kích hoạt hay khai thác thành công trong thực tế. Bộ tương thích (*adapter*) thực tế phải ghi rõ phiên bản/lược đồ, chế độ quét mã nguồn hay tệp nhị phân, độ bao phủ quét và quy tắc suy diễn chính sách từ các cảnh báo phát hiện.

### Giới hạn phân tích cần lưu ý

Khả năng phân tích tĩnh của `govulncheck` tập trung chủ yếu vào mã nguồn Go. Kỹ thuật xấp xỉ đồ thị cuộc gọi tĩnh có giới hạn trước reflection, hàm assembly hay điều phối động, không phân tích các phụ thuộc liên kết động qua CGO runtime, không lần vết trong plugin tải động (`plugin.Open`), và không quét các thư viện hệ thống nhị phân của ảnh nền container (như OpenSSL hay glibc; những thành phần này đòi hỏi công cụ quét ảnh container chuyên dụng).

### Thiết kế chính sách thông minh

`Reachable`, mức độ nghiêm trọng (*severity*), độ bao phủ của bộ quét và ngưỡng chấp nhận đều là dữ liệu đầu vào của chính sách. Một tổ chức có thể từ chối cảnh báo lỗ hổng mức cao hoặc nghiêm trọng nếu có thể vươn tới, tổ chức khác áp dụng ngoại lệ có thời hạn hoặc từ chối cả cảnh báo chưa chứng minh được đường gọi. Vì vậy `Reachable=false` không có nghĩa “an toàn”; trong bài thực hành nó chỉ dẫn tới trạng thái `WARN` theo chính sách minh họa và cần được xem xét lại trong chính sách thực tế.

---

## 4. Bất biến OCI: Mã băm Digest vs Nhãn Tag có thể biến đổi

Khi ảnh container được đóng gói và đẩy lên kho lưu trữ bản kê tiêu chuẩn OCI (như Docker Hub, AWS ECR, GitHub Packages), chúng ta thường gắn nhãn định danh phiên bản như `:latest` hoặc `:v1.2.3`.

Tuy nhiên, trong quy chuẩn đóng gói vùng chứa:
> Thẻ nhãn (`tag`) là con trỏ có thể thay đổi, trong khi chuỗi băm nội dung (`digest`) là định danh bất biến đại diện cho chính xác từng byte của hiện vật xuất phẩm (`artifact`).

![Tag có thể đổi đích và digest định danh nội dung](../../assets/diagrams/container-tag-digest.png)
@figure Thẻ nhãn (`tag`) được phân giải thành mã băm (`digest`) tại một thời điểm. Dùng mã băm cố định nội dung được tham chiếu, không tự xác minh người tạo hay độ an toàn của nội dung ấy.

Nếu thẻ nhãn (`tag`) bị trỏ sang ảnh khác, một thao tác kéo ảnh (*pull*) tiếp theo có thể nhận nội dung khác dù khuôn mẫu Pod vẫn giữ nguyên chuỗi thẻ nhãn đó. Kết quả còn phụ thuộc `imagePullPolicy`, bộ nhớ đệm của nút tính toán và chính sách của kho lưu trữ. Việc ghim mã băm nội dung giúp ràng buộc chính xác dữ liệu đã xét, nhưng không tự chứng minh bên tạo dựng hay bảo đảm gói phát hành vô hại.

Chính sách của bài thực hành chọn quy tắc đầu tiên:
Nguyên tắc cốt lõi: Từ chối mọi ảnh container không được định danh tường minh bằng mã băm SHA-256 dạng `sha256:<64_hex_chars>`.

---

## 5. Chữ ký số Sigstore/Cosign và Attestation SLSA

Làm sao chúng ta biết một ảnh container có mã băm `sha256:abc...` thực sự được tạo ra bởi quy trình CI chính thức của tổ chức chứ không phải do hacker tự biên dịch rồi đẩy lên?

Bộ công cụ Sigstore/Cosign là một lựa chọn cho việc ký và xác minh hiện vật xuất phẩm (`artifact`):

Một là, Ký không cần khóa tĩnh (*Keyless Signing*): Thay vì quản lý khóa bí mật dài hạn trên máy chủ CI, tiến trình thực thi tạo cặp khóa tạm thời cho mỗi lần ký và dùng mã xác thực OpenID Connect (OIDC) để xin chứng chỉ ngắn hạn từ Fulcio nhằm ràng buộc danh tính quy trình với khóa công khai.

Hai là, chứng chỉ ngắn hạn: Fulcio ràng buộc khóa công khai với danh tính OIDC theo chính sách của nhà cung cấp chứng chỉ (CA). `https://token.actions.githubusercontent.com` là bên phát hành (*issuer*), không phải danh tính riêng của quy trình. Bộ kiểm chứng phải xét cả danh tính chứng chỉ được phép, bên phát hành, thời hạn hiệu lực cùng bằng chứng xác minh tương ứng.

Ba là, Ký và xác minh khẳng định mã băm: Công cụ Cosign ký tải trọng chứa khẳng định (*claim*) về mã băm của ảnh; bộ kiểm chứng mặc định đối chiếu khẳng định đó cùng danh tính chứng chỉ theo chính sách. Quy trình này không đơn thuần chỉ là một lệnh gọi `ecdsa.VerifyASN1` trên chuỗi mã băm trong bài thực hành.

Bốn là, Bản chứng thực nguồn gốc `SLSA` (`SLSA Provenance`): Ngoài chữ ký số, đường ống CI còn tạo ra bản chứng thực xuất xứ (*provenance*) ghi rõ: mã băm commit nào, quy trình tự động nào (Builder ID) đã tạo ra gói phát hành.

---

## 6. Xây dựng Cổng chính sách Fail-Closed trong Go

Tại đây, toàn bộ các nguyên lý trên được hiện thực hóa vào một mô-đun Go theo mô hình chính sách kiểm chứng sư phạm.

Mô hình này không nhằm mục đích thay thế hay bao bọc toàn bộ mã nguồn của Cosign CLI hay SLSA verifier bên ngoài. Thay vào đó, nó tách bạch rõ ràng 3 khế ước giao tiếp (interfaces) cốt lõi của một hệ thống kiểm định chuỗi cung ứng hiện đại:

| Khế ước giao tiếp | Nhiệm vụ kỹ thuật |
| :--- | :--- |
| `SignatureVerifier` | Chịu trách nhiệm xác thực chữ ký số mật mã của image (Cosign / Notary). |
| `ProvenanceVerifier` | Chịu trách nhiệm kiểm chứng xuất xứ bản build (SLSA Provenance / in-toto). |
| `VulnerabilityProvider` | Chịu trách nhiệm cung cấp dữ liệu lỗ hổng (govulncheck / scanner). |

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

Đọc đoạn sau như một mô hình dùng dữ liệu mẫu đã tin cậy, không phải bộ xác minh danh tính thực thụ. Khóa công khai do bên gọi cung cấp; `Issuer` chỉ là chuỗi do bên gọi tự khai báo chứ chưa được ràng buộc với khóa bằng chứng chỉ số. `Attestation` cũng là cấu trúc chưa được xác thực. Một người tự tạo khóa, ký mã băm rồi sao chép bên phát hành/bên tạo dựng nằm trong danh sách trắng vẫn được mô hình chấp nhận. `TestModelAllowsSelfAssertedIdentity` giữ phản ví dụ này để ngăn việc hiểu nhầm kết quả kiểm thử đạt thành bằng chứng an toàn GitHub OIDC hay SLSA. Khi đưa vào cổng kiểm soát thực tế, phải thay các thành phần này bằng quy trình xác minh gốc tin cậy, định danh và xuất xứ đầy đủ; một phép so sánh chuỗi đơn thuần không thể lấp đầy lỗ hổng bảo mật này.

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

Tiếp theo, mô hình chính sách kiểm tra các trường thông tin xuất xứ đã được cung cấp. Trong hệ thống thực tế, bộ kiểm chứng phải xác thực chứng cứ trước khi chuyển vào cổng kiểm soát:

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
			"missing chứng thực nguồn gốc `SLSA` attestation",
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

Mã nguồn hoàn chỉnh của bài thực hành nằm tại thư mục `labs/part26-supply-chain-gate` (phân loại mức kiểm chứng: kiểm thử đơn vị đối với logic chính sách cổng đóng an toàn khi lỗi và chữ ký số ECDSA P-256 nội bộ, chứng minh khế ước an ninh của 7 kịch bản kiểm định mà không phụ thuộc vào hạ tầng mạng Sigstore bên ngoài). Khi chạy kiểm thử với cờ kiểm tra xung đột dữ liệu:

~~~bash
go test -v -race ./...
~~~

Bộ kiểm thử thực hiện xác minh toàn bộ 7 kịch bản:

~~~
=== RUN   TestPolicyGateAllowedWithValidSignature
--- PASS: TestPolicyGateAllowedWithValidSignature (0.00s)
=== RUN   TestModelAllowsSelfAssertedIdentity
--- PASS: TestModelAllowsSelfAssertedIdentity (0.00s)
=== RUN   TestPolicyGateDenyUnsignedImage
--- PASS: TestPolicyGateDenyUnsignedImage (0.00s)
=== RUN   TestPolicyGateDenyReachableVulnerability
--- PASS: TestPolicyGateDenyReachableVulnerability (0.00s)
=== RUN   TestPolicyGateAllowUncalledVulnerability
--- PASS: TestPolicyGateAllowUncalledVulnerability (0.00s)
=== RUN   TestPolicyGateFailClosedOnMutableTag
--- PASS: TestPolicyGateFailClosedOnMutableTag (0.00s)
=== RUN   TestPolicyGateStopsOnSignatureFailure
--- PASS: TestPolicyGateStopsOnSignatureFailure (0.00s)
PASS
ok      part26-supply-chain-gate   2.128s
~~~

### Phân tích các kịch bản kiểm thử

| Kịch bản fixture | Điều kiểm tra trong model | Quyết định (`Decision`) |
| :--- | :--- | :--- |
| Input được model chấp nhận | ECDSA tự tạo trong test; chuỗi issuer/builder khớp; không truyền finding. Không gọi GitHub OIDC hay scanner. | **ALLOW** theo policy model |
| Phản ví dụ tự khai danh tính (`TestModel...`) | Model chấp nhận key tự tạo và issuer/builder tự khai; chứng minh model chưa xác thực `OIDC` | **`ALLOW`** (nhấn mạnh ranh giới model) |
| Image không có chữ ký | Bị chặn đứng ngay tại Cửa 2 | **`DENY`** |
| Lỗ hổng nghiêm trọng có thể vươn tới (`Reachable = true`) | Ký hiệu `ssh.ParsePrivateKey` được gọi trong ứng dụng | **`DENY`** |
| Finding không được fixture đánh dấu reachable (`Reachable = false`) | `http2.Server.ServeConn` là tên symbol minh họa, không phải bằng chứng quan sát mọi đường chạy | **`ALLOW`** (kèm cảnh báo trong `Warnings`, theo policy lab) |
| Cố tình dùng tag thay vì digest | Truyền vào chuỗi `my-registry.io/app:v1.2.0` | Bị chặn ngay từ Cửa 1 → **`DENY`** |
| Dừng trước provenance sau lỗi chữ ký | Khi chữ ký sai, cổng dừng ngay tại Cửa 2 và không kiểm tra tiếp Cửa 3 | **`DENY`** (fail-closed tuần tự) |

---

## 8. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **Triển khai bằng Docker tag** (`:latest` hoặc `:v1.0.0`) thay vì sha256 digest. | Bị tấn công tráo đổi container image khi registry bị thỏa hiệp; pod scale up chạy phiên bản khác nhau. | Ghim (pin) mã băm bất biến `sha256:<hex>` trong Kubernetes Pod Spec. |
| **Nhận public key và issuer do caller tự khai mà coi là identity đã xác thực.** | Caller tự ký rồi khai issuer được phép; model vẫn có thể chấp nhận. | Dùng verifier thật kiểm tra trust roots, certificate identity/issuer và claim digest; so chuỗi không đủ. |
| **Thiết kế Cổng dạng Fail-Open:** Bỏ qua kiểm tra khi mạng tới OIDC/Registry bị timeout. | Khi mạng gặp sự cố, hệ thống tự động cho phép mọi image chưa được kiểm chứng đi thẳng vào production. | Luôn áp dụng nguyên tắc Fail-Closed: Bất kỳ lỗi mạng hay timeout nào cũng phải quy về `DENY`. |
| **Bỏ go.sum vì xem nó là file rác.** | Mất checksum đã ghi nhận trong project; không tự đồng nghĩa checksum database bị tắt. | Commit checksum khi có dependency; hiểu GOSUMDB/GOPRIVATE/replace. go mod verify kiểm tra cache, không quét mã độc. |

---

## 9. Bài tập thực hành thiết kế Cổng bảo vệ

### Thử thách 1: Ghim Base Image chuẩn (Golden Image Pinning)
Yêu cầu: Trong tệp Dockerfile nhiều tầng (multi-stage build), tầng thực thi cuối cùng thường bắt đầu bằng một ảnh cơ sở (`base image`, ví dụ `gcr.io/distroless/static-debian12`). Hãy viết một hàm Go nhận vào danh sách các ảnh cơ sở tin cậy (dưới dạng ánh xạ giữa tên image và mã băm sha256 cho phép) và kiểm tra xem một dòng `FROM <image>` trong Dockerfile có tuân thủ đúng mã băm đã được phê duyệt hay không.

### Thử thách 2: Cơ chế Timeout Fail-Closed (Network Timeout Fallback)
Yêu cầu: Khi cổng kiểm tra gọi sang máy chủ Rekor hoặc Fulcio qua mạng, nếu request bị timeout (quá 2 giây), hãy thiết kế một cấu trúc hàm sao cho: thay vì trả về lỗi chung không định danh, hàm phải trả về quyết định `DENY` kèm thông điệp đặc tả cơ chế: cổng kiểm soát chủ động từ chối theo nguyên tắc đóng an toàn (fail-closed) để bảo vệ cụm máy chủ.

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

Nguyên tắc đóng an toàn từ chối gói phát hành khi thiếu chứng cứ mà chính sách yêu cầu, kể cả lúc bộ kiểm chứng gặp sự cố gián đoạn dịch vụ. Cơ chế này không bảo đảm mọi gói phát hành được chấp nhận đều vô hại: gốc tin cậy, bên ký được phép, nội dung và chính quy tắc kiểm soát vẫn có thể sai sót hoặc bị xâm phạm. Tính an toàn và tính sẵn sàng của cổng kiểm soát là hai bài toán cần được kiểm chứng độc lập.

---

Quy trình kiểm soát chuỗi cung ứng phần mềm giúp đối chiếu tính toàn vẹn của mã nguồn, xuất xứ bản dựng và chữ ký số của ảnh container với chính sách đã chọn. Bằng chứng đó không chứng minh tệp nhị phân hoàn toàn vô hại: mã nguồn, bên ký hay gốc tin cậy vẫn có thể bị xâm phạm.

Khi vùng chứa thực sự vận hành, hệ thống cần bổ sung bằng chứng về hành vi lúc chạy: tiến trình nào mở kết nối mạng, đọc tệp cấu hình hay thực hiện các thao tác bất thường trong nhân hệ điều hành? Trong Chương 27, chúng ta sử dụng công nghệ eBPF kết hợp với Go để quan sát các sự kiện tại những điểm móc nối được chỉ định trong nhân hệ điều hành Linux. Đây không phải là khả năng bắt trọn mọi hành vi hay cơ chế quan sát miễn phí. Phạm vi điểm móc nối, cửa sổ thu thập, sự kiện bị đánh rơi và chi phí xử lý đều giới hạn phạm vi kết luận; kỹ sư bắt buộc phải đo lường độ trễ phụ trội với khối lượng tải thực tế trước khi triển khai trên môi trường vận hành.
