package controllers

import (
	"context"
	"testing"

	appsv1alpha1 "example.com/golang-master/part23-controller-runtime-operator/api/v1alpha1"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
)

func TestForeignDeploymentIsNotAdoptedOrMutated(t *testing.T) {
	for _, foreign := range []bool{false, true} {
		t.Run(map[bool]string{false: "unowned", true: "foreign-owner"}[foreign], func(t *testing.T) {
			scheme := setupTestScheme(t)
			app := &appsv1alpha1.AppService{ObjectMeta: metav1.ObjectMeta{Name: "same", Namespace: "default", UID: "our-uid", Finalizers: []string{AppServiceFinalizer}}, Spec: appsv1alpha1.AppServiceSpec{Image: "ours:v2", Replicas: 3}}
			replicas := int32(1)
			dep := &appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: "same", Namespace: "default"}, Spec: appsv1.DeploymentSpec{Replicas: &replicas, Template: corev1.PodTemplateSpec{Spec: corev1.PodSpec{Containers: []corev1.Container{{Name: "app", Image: "theirs:v1"}}}}}}
			if foreign {
				other := app.DeepCopy()
				other.UID = "foreign-uid"
				if err := controllerutil.SetControllerReference(other, dep, scheme); err != nil {
					t.Fatal(err)
				}
			}
			c := fake.NewClientBuilder().WithScheme(scheme).WithObjects(app, dep).WithStatusSubresource(app).Build()
			r := &AppServiceReconciler{Client: c, Scheme: scheme}
			key := types.NamespacedName{Namespace: "default", Name: "same"}
			if _, err := r.Reconcile(context.Background(), ctrl.Request{NamespacedName: key}); err == nil {
				t.Fatal("name collision must be rejected")
			}
			got := &appsv1.Deployment{}
			if err := c.Get(context.Background(), key, got); err != nil {
				t.Fatal(err)
			}
			if *got.Spec.Replicas != 1 || got.Spec.Template.Spec.Containers[0].Image != "theirs:v1" {
				t.Fatal("foreign deployment was mutated")
			}
		})
	}
}
