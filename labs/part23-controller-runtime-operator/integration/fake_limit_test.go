package integration

import (
	"context"
	"testing"

	app "example.com/golang-master/part23-controller-runtime-operator/api/v1alpha1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client/fake"
)

func TestFakeDoesNotProveGeneration(t *testing.T) {
	scheme := runtime.NewScheme()
	if err := app.AddToScheme(scheme); err != nil {
		t.Fatal(err)
	}
	a := &app.AppService{ObjectMeta: metav1.ObjectMeta{Name: "toy", Namespace: "default", Generation: 1}, Spec: app.AppServiceSpec{Image: "app:v1", Replicas: 1, Port: 8080}}
	c := fake.NewClientBuilder().WithScheme(scheme).WithStatusSubresource(&app.AppService{}).WithObjects(a).Build()
	ctx := context.Background()
	a.Spec.Image = "app:v2"
	if err := c.Update(ctx, a); err != nil {
		t.Fatal(err)
	}
	if a.Generation != 1 {
		t.Fatalf("fake behavior changed: generation=%d; revisit the comparison", a.Generation)
	}
	t.Log("MOCK_VERIFIED fake Update retains generation=1; this does not validate API-server generation semantics")
}
