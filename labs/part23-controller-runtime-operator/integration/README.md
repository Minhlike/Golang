# Fake lưu được object; API server thực thi contract

Test fake chỉ chứng minh behavior của client giả v0.25.1: sửa spec không tự
tăng generation. Không thay số ấy trong helper để đóng vai API server.

```powershell
go test -count=1 -v ./integration
```

`api_contract_test.go` có tag `integration && linux`, tạo control plane envtest
do test sở hữu cùng CRD riêng, không đọc kubeconfig hay kết nối cluster đang
có. Nạp schema ở `testdata`, create resource `reliability-contract` trong
namespace default của chính control plane ấy. Cleanup Stop trả process và
temporary data của envtest; không xóa cluster người dùng.

## Tái lập API thật trên Linux/WSL

Cần Go 1.27.1, binary envtest `kube-apiserver` và `etcd` tương thích Kubernetes
1.37.x có quyền execute. `k8s.io/* v0.37.0` và controller-runtime v0.25.1 đã có
trong module, không thêm dependency. Dùng asset đúng platform; không đổi sang
cluster cloud để vượt missing prerequisite.

```bash
cd labs/part23-controller-runtime-operator
export KUBEBUILDER_ASSETS=/path/to/k8s-1.37-assets
go test -tags integration -count=1 -v ./integration
RELIABILITY_MUTANT=root_status_write \
  go test -tags integration -count=1 \
  -run '^TestRealAPIContract$' -v ./integration
```

API test phải chứng minh create/root update bỏ status, status update giữ
spec/generation, spec update tăng generation 1→2, observedGeneration giữ 1,
và stale resourceVersion bị conflict. Mutant ghi status qua root endpoint phải
đỏ tại `status writer contract`; command exit 0 không đủ nếu test bị SKIP.
Không có arbitrary sleep: mỗi write đã hoàn tất được đọc lại bằng direct client.

## Trạng thái kiểm chứng hiện tại

`MOCK_VERIFIED`: fake generation test đã chạy. `NOT_RUN`: API server/etcd và
mutant API thật chưa chạy vì Windows thiếu Linux envtest assets. Pinned
controller-runtime có lỗi compile process helper khi import envtest trực tiếp
trên Windows; integration implementation chỉ build trên Linux, Windows stub
ghi SKIP/NOT_RUN minh bạch. Cross-compile Linux đã chạy thành công là
**COMPILE_ONLY**, không gắn nhãn INTEGRATION_TESTED.

Không có kubelet, scheduler, GC controller hay external finalizer trong envtest.
Do đó không suy Pod ready, child GC hay cloud cleanup từ suite này. Chương 17
và kind là bước kiểm định workload khác, không bị sửa bởi task này.

Evidence [commands/exit](../../../book/evidence/reliability-failure-paths/validation.log).
Contract theo [CRD status subresource](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/#status-subresource)
và [envtest v0.25.1](https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.25.1/pkg/envtest).
