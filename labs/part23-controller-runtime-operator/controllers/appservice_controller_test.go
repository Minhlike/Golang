package controllers

import (
	"context"
	"sync/atomic"
	"testing"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	appsv1alpha1 "example.com/golang-master/part23-controller-runtime-operator/api/v1alpha1"
)

type mockCleaner struct {
	cleaned atomic.Bool
}

func (m *mockCleaner) Cleanup(ctx context.Context, app *appsv1alpha1.AppService) error {
	m.cleaned.Store(true)
	return nil
}

func setupTestScheme(t *testing.T) *runtime.Scheme {
	s := runtime.NewScheme()
	if err := corev1.AddToScheme(s); err != nil {
		t.Fatalf("failed to add corev1 to scheme: %v", err)
	}
	if err := appsv1.AddToScheme(s); err != nil {
		t.Fatalf("failed to add appsv1 to scheme: %v", err)
	}
	if err := appsv1alpha1.AddToScheme(s); err != nil {
		t.Fatalf("failed to add appsv1alpha1 to scheme: %v", err)
	}
	return s
}

// TestReconcileCreateOwnedDeployment verifies child deployment creation and owner reference.
func TestReconcileCreateOwnedDeployment(t *testing.T) {
	scheme := setupTestScheme(t)

	app := &appsv1alpha1.AppService{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "cache-service",
			Namespace: "default",
		},
		Spec: appsv1alpha1.AppServiceSpec{
			Image:    "redis:7.2",
			Replicas: 3,
			Port:     6379,
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(app).
		WithStatusSubresource(app).
		Build()

	reconciler := &AppServiceReconciler{
		Client: fakeClient,
		Scheme: scheme,
	}

	req := ctrl.Request{
		NamespacedName: types.NamespacedName{
			Namespace: "default",
			Name:      "cache-service",
		},
	}

	// First pass adds finalizer and creates deployment
	res, err := reconciler.Reconcile(context.Background(), req)
	if err != nil {
		t.Fatalf("unexpected reconcile error: %v", err)
	}
	if !res.Requeue {
		t.Errorf("expected Requeue=true after creating child deployment")
	}

	// Verify deployment created
	dep := &appsv1.Deployment{}
	if err := fakeClient.Get(context.Background(), req.NamespacedName, dep); err != nil {
		t.Fatalf("failed to get expected child deployment: %v", err)
	}

	if *dep.Spec.Replicas != 3 {
		t.Errorf("expected 3 replicas, got %d", *dep.Spec.Replicas)
	}

	if len(dep.OwnerReferences) == 0 {
		t.Fatalf("expected OwnerReference on child deployment, got none")
	}
	if dep.OwnerReferences[0].Name != "cache-service" {
		t.Errorf("expected owner to be cache-service, got %s", dep.OwnerReferences[0].Name)
	}

	// Verify finalizer added to AppService
	updatedApp := &appsv1alpha1.AppService{}
	if err := fakeClient.Get(context.Background(), req.NamespacedName, updatedApp); err != nil {
		t.Fatalf("failed to fetch updated AppService: %v", err)
	}
	if !controllerutil.ContainsFinalizer(updatedApp, AppServiceFinalizer) {
		t.Errorf("expected finalizer %q on AppService", AppServiceFinalizer)
	}
}

// TestReconcileDriftCorrection verifies that unauthorized changes to child resources are corrected.
func TestReconcileDriftCorrection(t *testing.T) {
	scheme := setupTestScheme(t)

	app := &appsv1alpha1.AppService{
		ObjectMeta: metav1.ObjectMeta{
			Name:       "web-api",
			Namespace:  "prod",
			Finalizers: []string{AppServiceFinalizer},
		},
		Spec: appsv1alpha1.AppServiceSpec{
			Image:    "nginx:1.26",
			Replicas: 5,
			Port:     80,
		},
	}

	// Tampered child deployment with wrong replica count and image
	tamperedReplicas := int32(1)
	dep := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "web-api",
			Namespace: "prod",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &tamperedReplicas,
			Template: corev1.PodTemplateSpec{
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{Name: "app", Image: "malicious:v0"},
					},
				},
			},
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(app, dep).
		WithStatusSubresource(app).
		Build()

	reconciler := &AppServiceReconciler{
		Client: fakeClient,
		Scheme: scheme,
	}

	req := ctrl.Request{
		NamespacedName: types.NamespacedName{
			Namespace: "prod",
			Name:      "web-api",
		},
	}

	_, err := reconciler.Reconcile(context.Background(), req)
	if err != nil {
		t.Fatalf("reconcile error: %v", err)
	}

	// Verify drift corrected back to desired state
	correctedDep := &appsv1.Deployment{}
	if err := fakeClient.Get(context.Background(), req.NamespacedName, correctedDep); err != nil {
		t.Fatalf("failed to get corrected deployment: %v", err)
	}

	if *correctedDep.Spec.Replicas != 5 {
		t.Errorf("expected replicas reset to 5, got %d", *correctedDep.Spec.Replicas)
	}
	if correctedDep.Spec.Template.Spec.Containers[0].Image != "nginx:1.26" {
		t.Errorf("expected image reset to nginx:1.26, got %s", correctedDep.Spec.Template.Spec.Containers[0].Image)
	}
}

// TestReconcileFinalizerExecution verifies external cleanup and finalizer removal upon deletion.
func TestReconcileFinalizerExecution(t *testing.T) {
	scheme := setupTestScheme(t)

	now := metav1.NewTime(time.Now())
	app := &appsv1alpha1.AppService{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "legacy-service",
			Namespace:         "default",
			DeletionTimestamp: &now,
			Finalizers:        []string{AppServiceFinalizer},
		},
		Spec: appsv1alpha1.AppServiceSpec{
			Image:    "legacy:1.0",
			Replicas: 1,
		},
	}

	cleaner := &mockCleaner{}
	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(app).
		WithStatusSubresource(app).
		Build()

	reconciler := &AppServiceReconciler{
		Client:          fakeClient,
		Scheme:          scheme,
		ExternalCleaner: cleaner,
	}

	req := ctrl.Request{
		NamespacedName: types.NamespacedName{
			Namespace: "default",
			Name:      "legacy-service",
		},
	}

	_, err := reconciler.Reconcile(context.Background(), req)
	if err != nil {
		t.Fatalf("reconcile error during finalization: %v", err)
	}

	if !cleaner.cleaned.Load() {
		t.Errorf("expected external cleaner to be invoked, but was not")
	}

	// Verify finalizer was removed and object was purged from storage
	updatedApp := &appsv1alpha1.AppService{}
	err = fakeClient.Get(context.Background(), req.NamespacedName, updatedApp)
	if err == nil {
		if controllerutil.ContainsFinalizer(updatedApp, AppServiceFinalizer) {
			t.Errorf("expected finalizer to be removed, but still present")
		}
	} else if !errors.IsNotFound(err) {
		t.Fatalf("unexpected error fetching AppService: %v", err)
	}
}

// TestReconcileStatusSubresource verifies status calculation without mutating spec.
func TestReconcileStatusSubresource(t *testing.T) {
	scheme := setupTestScheme(t)

	app := &appsv1alpha1.AppService{
		ObjectMeta: metav1.ObjectMeta{
			Name:       "payment-gw",
			Namespace:  "fin",
			Finalizers: []string{AppServiceFinalizer},
		},
		Spec: appsv1alpha1.AppServiceSpec{
			Image:    "payment:v2",
			Replicas: 3,
			Port:     8080,
		},
	}

	depReplicas := int32(3)
	dep := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "payment-gw",
			Namespace: "fin",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &depReplicas,
			Template: corev1.PodTemplateSpec{
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{Name: "app", Image: "payment:v2"}},
				},
			},
		},
		Status: appsv1.DeploymentStatus{
			AvailableReplicas: 3,
		},
	}

	fakeClient := fake.NewClientBuilder().
		WithScheme(scheme).
		WithObjects(app, dep).
		WithStatusSubresource(app).
		Build()

	reconciler := &AppServiceReconciler{
		Client: fakeClient,
		Scheme: scheme,
	}

	req := ctrl.Request{
		NamespacedName: types.NamespacedName{
			Namespace: "fin",
			Name:      "payment-gw",
		},
	}

	_, err := reconciler.Reconcile(context.Background(), req)
	if err != nil {
		t.Fatalf("reconcile error: %v", err)
	}

	updatedApp := &appsv1alpha1.AppService{}
	if err := fakeClient.Get(context.Background(), req.NamespacedName, updatedApp); err != nil {
		t.Fatalf("failed to get app: %v", err)
	}

	if updatedApp.Status.AvailableReplicas != 3 {
		t.Errorf("expected AvailableReplicas=3, got %d", updatedApp.Status.AvailableReplicas)
	}
	if updatedApp.Status.Phase != "Ready" {
		t.Errorf("expected Phase='Ready', got %s", updatedApp.Status.Phase)
	}
}

// TestNotFoundResourceNoOp verifies reconciler gracefully ignores deleted resources.
func TestNotFoundResourceNoOp(t *testing.T) {
	scheme := setupTestScheme(t)
	fakeClient := fake.NewClientBuilder().WithScheme(scheme).Build()

	reconciler := &AppServiceReconciler{
		Client: fakeClient,
		Scheme: scheme,
	}

	req := ctrl.Request{
		NamespacedName: types.NamespacedName{
			Namespace: "default",
			Name:      "ghost-resource",
		},
	}

	res, err := reconciler.Reconcile(context.Background(), req)
	if err != nil {
		t.Fatalf("expected nil error on not found, got: %v", err)
	}
	if res.Requeue || res.RequeueAfter > 0 {
		t.Errorf("expected empty result, got: %+v", res)
	}
}
