# Đúng certificate chưa có nghĩa được phép ghi

Runtime tạo CA/certificate bằng stdlib, server TLS ở loopback, key chỉ trong
RAM. Client dùng CA riêng và `ServerName=service.test` theo DNS SAN; không dùng
OS root store, network public, file secret hay bỏ verification. Policy lab
chọn TLS 1.3 và RequireAndVerifyClientCert, không áp đặt cho mọi deployment.

Đọc `TestCertificateBoundaries` và `TestAuthorizationContract` trước source.

```powershell
# Từ labs/part11-request-path
go test -count=1 -v ./identity
go test -race -count=1 ./identity
go vet ./identity
$env:RELIABILITY_MUTANT='trust_equals_role'
go test -count=1 -run '^TestAuthorizationContract$' ./identity
Remove-Item Env:RELIABILITY_MUTANT
```

Mutant phải exit 1 vì authenticated reader ghi được và effect counter tăng.
Test không gửi mutation với key thật. Bản đúng phải từ chối server CA lạ,
hostname/SAN sai, thiếu client cert, client CA lạ, expired client và wrong EKU;
không side effect nào được thực hiện. Client error type được đối chiếu cho
unknown authority/hostname; không pin chuỗi alert từ peer qua các version.

Reader được đọc nhưng không được ghi; operator được ghi đúng một lần ở happy
path. Một leaf được CA tin ký nhưng identity không thuộc allowlist, hoặc thiếu
URI identity, vẫn phải nhận 403. `X-Role: admin` không được dùng. Policy chỉ
đọc `VerifiedChains`, không tự tin `PeerCertificates` hay `Subject.CommonName`.

`REAL_LOCAL_VERIFIED` là TLS handshake/HTTP loopback với certificate runtime.
`UNIT_TESTED` kiểm tra policy thiếu verified chain. Kênh TLS xác thực certificate
và bảo vệ traffic; quyền action vẫn là mapping của application. Chưa kiểm
rotation, revocation, CA compromise, proxy identity propagation, OAuth hay
MCP HTTP deployment. mTLS không phải yêu cầu chung cho mọi MCP transport.

Evidence: [actual output](../../../book/evidence/reliability-failure-paths/validation.log).
API đã pin: [tls Go 1.27.1](https://pkg.go.dev/crypto/tls@go1.27.1#Config),
[x509 Go 1.27.1](https://pkg.go.dev/crypto/x509@go1.27.1#Certificate.VerifyHostname).
