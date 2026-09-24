# Chương 23 — Từ controller đến operator: API riêng và vòng đời tài nguyên

Trong Chương 22, chúng ta đã nắm vững nền móng của một controller cấp thấp: dùng `client-go`, `SharedInformer` và `TypedRateLimitingInterface` để điều hòa các tài nguyên lõi như Pod. Nhưng khi hệ thống phát triển, nhu cầu quản trị hạ tầng vượt xa các khối cơ bản của Kubernetes.

Bạn không chỉ muốn quản lý Pod đơn lẻ; bạn muốn định nghĩa cả một hệ sinh thái: một cụm cơ sở dữ liệu phân tán tự động sao lưu định kỳ, một dịch vụ thanh toán tự động cấp phát tài nguyên trên đám mây, hoặc một ứng dụng nội bộ tự động cấu hình ingress, chứng chỉ SSL và tài khoản IAM.

Nếu làm theo cách thủ công, bạn phải bảo trì hàng trăm file YAML dài vô tận và phụ thuộc vào con người chạy lệnh `kubectl apply`. Đây chính là lúc khái niệm **Operator** ra đời: *đóng gói tri thức của một kỹ sư vận hành giàu kinh nghiệm (Domain Operational Knowledge) vào trong mã nguồn Go tự động*.

---

## 1. Operator là gì và Khi nào cần Operator?

Câu hỏi trung tâm của chương này là:
> *Sự khác biệt cốt lõi giữa một Kubernetes Controller thông thường và một Kubernetes Operator là gì?*

Mọi Operator đều là Controller, nhưng không phải mọi Controller đều là Operator:

1. **Controller thông thường:** Thường làm việc với các tài nguyên dựng sẵn của Kubernetes (`Pod`, `Deployment`, `Service`, `ConfigMap`). Nó chỉ hiểu các khái niệm hạ tầng chung chung.
2. **Operator:** Kết hợp giữa **Custom Resource Definition (CRD)** — một API hoàn toàn mới do bạn tự định nghĩa cho bài toán của mình — và một **Dedicated Controller** mang tri thức nghiệp vụ chuyên sâu.

~~~
Tri thức chuyên gia (Domain Knowledge)
      │ (Đóng gói vào mã nguồn Go)
      ▼
[Kubernetes Operator]
      ├── 1. CRD              ──> Khai báo ý định
      ├── 2. Controller       ──> Vòng lặp điều hòa
      └── 3. Tích hợp ngoài   ──> Quản trị vòng đời
~~~

Thay vì bắt người dùng phải tự tạo `Deployment`, gắn `ConfigMap`, tạo `Secret` và mở `Service`, Operator cung cấp một tài nguyên duy nhất gọn gàng:

~~~yaml
apiVersion: apps.example.com/v1alpha1
kind: AppService
metadata:
  name: payment-api
spec:
  image: "payment:v2.4.0"
  replicas: 3
  port: 8080
~~~

Khi bạn nộp khai báo trên, Operator sẽ tự động sinh ra Deployment tương ứng, gắn nhãn, cấu hình health check, theo dõi sức khỏe và cập nhật trạng thái thực tế về cho bạn.

---

## 2. Kiến trúc của controller-runtime

Viết Operator bằng `client-go` thuần túy đòi hỏi hàng ngàn dòng code chỉ để thiết lập Reflector, Informer, Indexer và WorkQueue. Để giải phóng kỹ sư khỏi sự phức tạp lặp lại này, cộng đồng Kubernetes chính thức xây dựng thư viện `sigs.k8s.io/controller-runtime`.

Sơ đồ phân nhánh dưới đây mô tả cấu trúc của một hệ thống Operator hiện đại:

~~~
[Custom Resource: AppService]
              │
              ▼
   [controller-runtime Manager]
   ├── Scheme:       Ánh xạ Go Struct <-> GVK
   ├── SharedCache:  Đọc snapshot cực nhanh (In-Memory)
   ├── SplitClient:  Đọc từ Cache / Ghi thẳng API Server
   └── Controller:   Hàng đợi và phân phối Reconcile
              │
              ▼
    [Reconciler Function]
    (ctx context.Context, req ctrl.Request)
              │
              ├───> Đọc Trạng thái Thực tế (Get từ Cache)
              ├───> Dọn dẹp ngoại vi nếu có DeletionTimestamp
              ├───> Tạo / Điều chỉnh Tài nguyên Con (Deployment)
              └───> Cập nhật Status (r.Status().Update)
~~~

### Bốn trụ cột của controller-runtime

1. **Manager:** Thùng chứa (container) quản lý vòng đời của toàn bộ tiến trình Operator: quản lý các bộ nhớ đệm dùng chung, cơ chế bầu chọn trưởng cụm (leader election), máy chủ metric Prometheus và kiểm tra sức khỏe (health probes).
2. **Scheme:** Bảng đăng ký ánh xạ giữa Go struct (`v1alpha1.AppService`) và định danh `GroupVersionKind` (`apps.example.com/v1alpha1, Kind=AppService`) của Kubernetes.
3. **Split Client:** Bộ client thông minh với cơ chế phân tách:
   - Các thao tác đọc (`Get`, `List`): Luôn truy vấn vào Informer Cache cục bộ, tiêu tốn 0 request HTTP tới API Server.
   - Các thao tác ghi (`Create`, `Update`, `Delete`, `Patch`): Gửi trực tiếp đến API Server để bảo đảm tính nhất quán dữ liệu.
4. **Reconciler:** Interface tối giản chứa một hàm duy nhất `Reconcile(ctx, req)`. Khác với `client-go`, hàm này chỉ nhận vào struct `ctrl.Request` chứa `NamespacedName (namespace/name)` của tài nguyên cần điều hòa.

---

## 3. Bản thiết kế CRD: Ranh giới rạch ròi giữa Spec và Status

Một trong những quy tắc bất biến trong thiết kế API Kubernetes là sự phân lập triệt để giữa **Spec** và **Status**:

| Khối dữ liệu | Ý nghĩa | Ai có quyền ghi? | Trách nhiệm |
| :--- | :--- | :--- | :--- |
| **Spec** | Trạng thái mong muốn (Desired State). | Người dùng, Helm, CI/CD pipeline, GitOps (ArgoCD). | Khai báo hệ thống cần đạt được điều gì. |
| **Status** | Trạng thái quan sát được (Observed State). | Duy nhất **Operator Controller** chịu trách nhiệm. | Báo cáo thực tế hệ thống đang chạy ra sao. |

### Quy tắc chống trượt (Anti-Drift Rule)

> **CẤM TUYỆT ĐỐI:** Reconciler không bao giờ được phép tự ý thay đổi dữ liệu trong `Spec` của Custom Resource!

Nếu người dùng cấu hình `replicas: 3`, mà Reconciler thấy tải cao rồi tự ý sửa `spec.replicas = 5`, hệ thống sẽ rơi vào cuộc chiến bất tận giữa Operator và công cụ GitOps (ArgoCD liên tục kéo về 3, Operator liên tục đẩy lên 5).

Mọi kết quả quan sát (số replica đang sẵn sàng, phiên bản thực tế đang chạy, điều kiện lỗi) bắt buộc phải ghi vào trường `Status`.

### Phân lập Status Subresource

Để bảo vệ ranh giới này, Kubernetes cung cấp cơ chế **Status Subresource** (`/status` endpoint). Khi cập nhật trạng thái, bạn phải gọi:

~~~go
// ĐÚNG: Chỉ sửa Status, không đổi metadata.generation
if err := r.Status().Update(ctx, appService); err != nil {
	return ctrl.Result{}, err
}
~~~

Nếu bạn gọi nhầm `r.Update(ctx, appService)`, Kubernetes sẽ coi đó là một thay đổi trên toàn bộ đối tượng, làm tăng biến đếm `metadata.generation`, và phát ra sự kiện kích hoạt hàm `Reconcile` chạy lại. Điều này dễ dẫn đến vòng lặp vô tận (reconcile loop storm).

---

## 4. Quản lý tài nguyên con: OwnerReferences và Garbage Collection

Khi `AppService` sinh ra một `Deployment`, làm sao để Kubernetes biết hai đối tượng này có quan hệ cha - con?

Câu trả lời là **OwnerReference** (Tham chiếu chủ sở hữu). Thư viện `controller-runtime` cung cấp hàm chuẩn hóa:

~~~go
if err := controllerutil.SetControllerReference(
	appService, newDeployment, r.Scheme,
); err != nil {
	return fmt.Errorf("không thể gán owner reference: %w", err)
}
~~~

### Lợi ích tối cao của OwnerReference:

1. **Tự động dọn dẹp (Cascading Deletion):** Khi người dùng xóa `AppService`, bộ dọn rác (Garbage Collector) của Kubernetes tự động xóa tất cả `Deployment`, `Pod`, `Service` con thuộc về nó mà Operator không cần viết thêm dòng code nào.
2. **Theo dõi sự kiện ngược dòng (Watch Events):** Controller có thể cấu hình `Watches(&appsv1.Deployment{}, handler.EnqueueRequestForOwner(...))`. Bất cứ khi nào ai đó sửa đổi hoặc xóa Deployment con, sự kiện sẽ tự động ánh xạ ngược về `AppService` cha để Reconciler thức dậy sửa chữa.

---

## 5. Finalizer: Cổng gác vòng đời và Dọn dẹp tài nguyên ngoại vi

Nếu `OwnerReference` giải quyết xuất sắc việc dọn dẹp các tài nguyên nội bộ trong Kubernetes, thì điều gì sẽ xảy ra nếu ứng dụng của bạn tạo ra các tài nguyên bên ngoài cụm?
- Một cơ sở dữ liệu Amazon RDS hoặc Google Cloud SQL.
- Một bản ghi DNS trên Cloudflare.
- Một hàng đợi tin nhắn AWS SQS.

Khi người dùng chạy `kubectl delete appservice payment-api`, nếu Kubernetes xóa ngay đối tượng khỏi etcd, Operator sẽ mất dấu vĩnh viễn và không còn biết tài nguyên đám mây nào cần phải thu hồi, gây lãng phí hàng nghìn USD chi phí hạ tầng.

Đây chính là sứ mệnh của **Finalizer** (Bộ chốt vòng đời).

~~~
1. Khởi tạo tài nguyên:
   AddFinalizer("apps.example.com/finalizer") ──> Lưu vào etcd

2. Người dùng gõ "kubectl delete":
   API Server KHÔNG XÓA NGAY!
   Set deletionTimestamp = "2026-09-24T12:00:00Z"
   Tài nguyên chuyển sang trạng thái "Terminating"

3. Reconciler thức dậy:
   Thấy deletionTimestamp != nil
   ──> Thực thi dọn dẹp tài nguyên đám mây
   ──> Dọn dẹp thành công?
       ──(Có)──> RemoveFinalizer(...) ──> etcd xóa hẳn!
       ──(Lỗi)──> Giữ nguyên Finalizer ──> Thử lại sau
~~~

### Cạm bẫy Finalizer Deadlock

Một lỗi vận hành nghiêm trọng là thiết kế hàm dọn dẹp không có tính **lũy đẳng (idempotency)**. Nếu dịch vụ đám mây trả về lỗi `404 Not Found` (nghĩa là tài nguyên đã bị ai đó xóa trước rồi), hàm dọn dẹp không được coi đó là lỗi! 

Nếu bạn trả về lỗi khi gặp 404, Reconciler sẽ liên tục thử lại và không bao giờ chịu gỡ Finalizer. Tài nguyên Kubernetes sẽ bị kẹt vĩnh viễn ở trạng thái `Terminating` và không ai có thể xóa được.

---

## 6. Hiện thực Operator hoàn chỉnh trong Go

Dưới đây là phần mã nguồn hiện thực bộ Reconciler chuẩn mực được trích xuất từ dự án `labs/part23-controller-runtime-operator/`:

Định nghĩa cấu trúc điều hòa với khả năng tiêm phụ thuộc (Dependency Injection) cho bộ dọn dẹp ngoại vi:

~~~go
const AppServiceFinalizer = "apps.example.com/finalizer"

type ExternalCleaner interface {
	Cleanup(
		ctx context.Context, app *appsv1alpha1.AppService,
	) error
}

type AppServiceReconciler struct {
	client.Client
	Scheme          *runtime.Scheme
	ExternalCleaner ExternalCleaner
}
~~~

### Vòng lặp điều hòa trung tâm

Hàm `Reconcile` điều phối toàn bộ vòng đời: từ kiểm tra xóa, tạo tài nguyên con, đến sửa chữa sai lệch cấu hình:

~~~go
func (r *AppServiceReconciler) Reconcile(
	ctx context.Context, req ctrl.Request,
) (ctrl.Result, error) {
	appService := &appsv1alpha1.AppService{}
	err := r.Get(ctx, req.NamespacedName, appService)
	if err != nil {
		if errors.IsNotFound(err) {
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, err
	}

	// 1. Xử lý Finalizer: Kiểm soát vòng đời xóa
	if !appService.DeletionTimestamp.IsZero() {
		return r.handleDeletion(ctx, appService)
	}

	// Đảm bảo đối tượng luôn có Finalizer bảo vệ
	if !controllerutil.ContainsFinalizer(
		appService, AppServiceFinalizer,
	) {
		controllerutil.AddFinalizer(
			appService, AppServiceFinalizer,
		)
		return ctrl.Result{}, r.Update(ctx, appService)
	}

	// 2. Điều hòa Deployment con và sửa sai lệch (Drift)
	if err := r.reconcileDeployment(
		ctx, appService,
	); err != nil {
		return ctrl.Result{}, err
	}

	// 3. Cập nhật Status Subresource
	return ctrl.Result{}, r.updateStatus(ctx, appService)
}
~~~

### Xử lý Xóa an toàn và Dọn dẹp ngoại vi

~~~go
func (r *AppServiceReconciler) handleDeletion(
	ctx context.Context, app *appsv1alpha1.AppService,
) (ctrl.Result, error) {
	hasFin := controllerutil.ContainsFinalizer(
		app, AppServiceFinalizer,
	)
	if hasFin {
		if r.ExternalCleaner != nil {
			err := r.ExternalCleaner.Cleanup(ctx, app)
			if err != nil {
				return ctrl.Result{}, fmt.Errorf(
					"cleanup lỗi: %w", err,
				)
			}
		}
		// Dọn dẹp xong -> Gỡ finalizer để etcd dọn dẹp
		controllerutil.RemoveFinalizer(
			app, AppServiceFinalizer,
		)
		if err := r.Update(ctx, app); err != nil {
			return ctrl.Result{}, err
		}
	}
	return ctrl.Result{}, nil
}
~~~

### Tự động nhận diện và sửa chữa sai lệch (Drift Correction)

Nếu ai đó dùng `kubectl scale` để sửa số replica của Deployment con từ 3 xuống 1, Reconciler phát hiện sự không đồng nhất giữa `appService.Spec.Replicas` và `deployment.Spec.Replicas`, từ đó tự động ép trạng thái về đúng bản thiết kế ban đầu:

~~~go
func (r *AppServiceReconciler) syncDeploymentDrift(
	app *appsv1alpha1.AppService, dep *appsv1.Deployment,
) bool {
	drifted := false
	if dep.Spec.Replicas == nil ||
		*dep.Spec.Replicas != app.Spec.Replicas {
		dep.Spec.Replicas = &app.Spec.Replicas
		drifted = true
	}
	if len(dep.Spec.Template.Spec.Containers) > 0 {
		c := &dep.Spec.Template.Spec.Containers[0]
		if c.Image != app.Spec.Image {
			c.Image = app.Spec.Image
			drifted = true
		}
	}
	return drifted
}
~~~

---

## 7. Bằng chứng kiểm thử: Chứng minh 5 quy luật Operator

Bộ kiểm thử tại `labs/part23-controller-runtime-operator/controllers/appservice_controller_test.go` sử dụng `fake.NewClientBuilder()` để mô phỏng toàn diện cụm Kubernetes API Server:

~~~
=== RUN   TestReconcileCreateOwnedDeployment
--- PASS: TestReconcileCreateOwnedDeployment (0.51s)
=== RUN   TestReconcileDriftCorrection
--- PASS: TestReconcileDriftCorrection (0.01s)
=== RUN   TestReconcileFinalizerExecution
--- PASS: TestReconcileFinalizerExecution (0.01s)
=== RUN   TestReconcileStatusSubresource
--- PASS: TestReconcileStatusSubresource (0.01s)
=== RUN   TestNotFoundResourceNoOp
--- PASS: TestNotFoundResourceNoOp (0.01s)
PASS
ok      part23-controller-runtime-operator/controllers   1.875s
~~~

### 1. Khởi tạo tài nguyên con kèm OwnerReference (TestReconcileCreateOwnedDeployment)
Khi tạo mới một `AppService`, Reconciler tự động sinh một `Deployment` mang tên tương ứng. Bằng chứng kiểm thử xác nhận `dep.OwnerReferences[0].Name == "cache-service"`, và `app.Finalizers` lập tức được bổ sung khóa `apps.example.com/finalizer`.

### 2. Tự phục hồi sai lệch cấu hình (TestReconcileDriftCorrection)
Giả lập một hành vi can thiệp trái phép: sửa thủ công Deployment thành `replicas: 1` và đổi ảnh thành `malicious:v0`. Khi hàm `Reconcile` chạy, nó phát hiện sai lệch và khôi phục ngay lập tức về `replicas: 5` và `image: "nginx:1.26"`.

### 3. Vòng đời Finalizer và Xóa sạch dữ liệu (TestReconcileFinalizerExecution)
Gán `DeletionTimestamp` vào đối tượng. Reconciler kích hoạt hàm `ExternalCleaner.Cleanup()`, sau đó xóa Finalizer. Fake client mô phỏng chính xác hành vi của Kubernetes: ngay khi finalizer cuối cùng biến mất, đối tượng bị thu hồi hoàn toàn khỏi bộ nhớ etcd (`errors.IsNotFound` trả về true).

### 4. Cập nhật Status Subresource độc lập (TestReconcileStatusSubresource)
Kiểm chứng rằng khi Deployment con đạt trạng thái sẵn sàng (`AvailableReplicas: 3`), Reconciler cập nhật `appService.Status.AvailableReplicas = 3` và gán nhãn `Phase = "Ready"` thông qua cổng `r.Status().Update()` mà không làm biến đổi bất kỳ trường nào trong `Spec`.

### 5. An toàn khi tài nguyên biến mất (TestNotFoundResourceNoOp)
Gửi yêu cầu điều hòa cho một tài nguyên không hề tồn tại. Reconciler trả về `(ctrl.Result{}, nil)` một cách nhẹ nhàng, không gây panic hay sinh lỗi rác trong log hệ thống.

---

## 8. Các cạm bẫy người học thường gặp (Learner Pitfalls)

| Cạm bẫy thực tế | Hậu quả trên Production | Giải pháp phòng ngừa |
| :--- | :--- | :--- |
| **Sửa trường Spec trong Reconcile** để lưu trạng thái tạm thời. | Xung đột vĩnh viễn với các công cụ GitOps (ArgoCD), gây ra bão điều hòa liên tục. | Chỉ đọc `Spec`. Mọi trạng thái vận hành phải lưu tại nhánh `Status`. |
| **Dùng r.Update thay vì r.Status().Update** khi cập nhật trạng thái. | Làm tăng số `metadata.generation`, kích hoạt Reconcile chạy lại vô tận. | Luôn tách bạch: cập nhật dữ liệu qua `r.Update()`, cập nhật trạng thái qua `r.Status().Update()`. |
| **Xử lý Finalizer không lũy đẳng (Non-idempotent)** khi dịch vụ ngoài báo 404. | Tài nguyên bị kẹt vĩnh viễn ở trạng thái `Terminating`, cụm máy chủ không thể dọn rác. | Nếu lệnh xóa ngoại vi trả về 404 Not Found, coi như đã xóa thành công và gỡ Finalizer. |
| **Quên gán OwnerReference** cho tài nguyên con do Operator sinh ra. | Khi xóa đối tượng cha, tài nguyên con bị mồ côi (orphaned), gây rò rỉ tài nguyên cụm. | Luôn gọi `controllerutil.SetControllerReference(owner, child, r.Scheme)` trước khi tạo. |

---

## 9. Bài tập thực hành thiết kế Operator

### Thử thách 1: Tự động khởi tạo ConfigMap đi kèm Deployment
**Yêu cầu:** Mở rộng `AppServiceReconciler` để mỗi khi tạo một `AppService`, nó tự động tạo thêm một `ConfigMap` chứa file cấu hình ứng dụng (`app.json`). `ConfigMap` này cũng phải được gắn `OwnerReference` trỏ về `AppService`.

### Thử thách 2: Báo cáo Condition chuẩn mực trong Status
**Yêu cầu:** Kubernetes khuyến nghị sử dụng slice `[]metav1.Condition` để thể hiện trạng thái chi tiết của tài nguyên. Hãy bổ sung hàm trợ giúp để cập nhật Condition `Type="DeploymentReady"` với `Status="True"` khi số lượng Pod sẵn sàng bằng số lượng replica mong muốn, hoặc `Status="False"` kèm Reason `"ReplicasUnavailable"` khi chưa đủ.

---

## 10. Hướng dẫn giải và Phân tích kiến trúc bài tập

### Lời giải Thử thách 1: Đồng bộ ConfigMap con

~~~go
func (r *AppServiceReconciler) reconcileConfigMap(
	ctx context.Context, app *appsv1alpha1.AppService,
) error {
	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      app.Name + "-config",
			Namespace: app.Namespace,
		},
		Data: map[string]string{
			"port": fmt.Sprintf("%d", app.Spec.Port),
		},
	}

	// Gán quan hệ cha con để tự động xóa khi app bị xóa
	if err := controllerutil.SetControllerReference(
		app, cm, r.Scheme,
	); err != nil {
		return err
	}

	found := &corev1.ConfigMap{}
	key := client.ObjectKeyFromObject(cm)
	err := r.Get(ctx, key, found)
	if errors.IsNotFound(err) {
		return r.Create(ctx, cm)
	}
	return err
}
~~~

### Lời giải Thử thách 2: Quản lý Condition bằng meta.SetStatusCondition

Sử dụng thư viện chuẩn `k8s.io/apimachinery/pkg/api/meta`:

~~~go
import "k8s.io/apimachinery/pkg/api/meta"

func (r *AppServiceReconciler) updateConditions(
	app *appsv1alpha1.AppService, isReady bool,
) {
	condition := metav1.Condition{
		Type:               "DeploymentReady",
		Status:             metav1.ConditionFalse,
		Reason:             "ReplicasUnavailable",
		Message:            "Chưa đủ bản sao sẵn sàng",
		LastTransitionTime: metav1.Now(),
	}

	if isReady {
		condition.Status = metav1.ConditionTrue
		condition.Reason = "DeploymentAvailable"
		condition.Message = "Tất cả bản sao đều khỏe mạnh"
	}

	meta.SetStatusCondition(
		&app.Status.Conditions, condition,
	)
}
~~~

Hàm `meta.SetStatusCondition` tự động kiểm tra: nếu điều kiện đã tồn tại và không thay đổi trạng thái, nó sẽ giữ nguyên trường `LastTransitionTime` cũ, giúp hệ thống theo dõi chính xác thời điểm chuyển giao trạng thái.

---

Bằng việc kết hợp giữa **Custom Resource**, **controller-runtime** và **Finalizer**, bạn đã làm chủ công nghệ cốt lõi đứng sau các Operator phức tạp nhất thế giới hiện nay như Prometheus Operator, Kafka Strimzi hay cert-manager. Trong Chương 24, chúng ta sẽ mở rộng tầm nhìn ra ngoài biên giới Kubernetes: xây dựng các hệ thống tự động hóa hạ tầng đám mây trên **AWS SDK for Go v2** mà không bao giờ biến thông tin xác thực thành bí mật dài hạn dễ bị lộ lọt.
