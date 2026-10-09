//go:build integration && linux

package integration

import (
	"context"
	"os"
	"path/filepath"
	"runtime"
	"testing"
	"time"

	app "example.com/golang-master/part23-controller-runtime-operator/api/v1alpha1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	k8sruntime "k8s.io/apimachinery/pkg/runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/envtest"
)

// Starts a NEW owned control plane; never reads a user's kubeconfig or cluster.
// envtest does NOT start kubelet, scheduler or garbage collector.
func TestRealAPIContract(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("NOT_RUN: Linux envtest assets required; run in WSL/Linux, not against an existing cluster")
	}
	assets := os.Getenv("KUBEBUILDER_ASSETS")
	for _, name := range []string{"kube-apiserver", "etcd"} {
		if assets == "" {
			t.Skip("NOT_RUN: set KUBEBUILDER_ASSETS to owned Kubernetes 1.37.x Linux assets")
		}
		info, err := os.Stat(filepath.Join(assets, name))
		if err != nil || info.IsDir() {
			t.Skipf("NOT_RUN: missing asset %s in %s", name, assets)
		}
	}
	e := &envtest.Environment{BinaryAssetsDirectory: assets,
		CRDDirectoryPaths: []string{filepath.Join("testdata")}, ErrorIfCRDPathMissing: true}
	config, err := e.Start()
	if err != nil {
		_ = e.Stop()
		t.Fatalf("control plane failed, NOT VERIFIED: %v", err)
	}
	t.Cleanup(func() {
		if err := e.Stop(); err != nil {
			t.Error(err)
		}
	})
	scheme := k8sruntime.NewScheme()
	if err := app.AddToScheme(scheme); err != nil {
		t.Fatal(err)
	}
	c, err := client.New(config, client.Options{Scheme: scheme})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	a := &app.AppService{ObjectMeta: metav1.ObjectMeta{Name: "reliability-contract", Namespace: "default"}, Spec: app.AppServiceSpec{Image: "app:v1", Replicas: 1, Port: 8080}, Status: app.AppServiceStatus{Phase: "forged"}}
	if err := c.Create(ctx, a); err != nil {
		t.Fatal(err)
	}
	key := client.ObjectKeyFromObject(a)
	get := func() *app.AppService {
		t.Helper()
		v := new(app.AppService)
		if err := c.Get(ctx, key, v); err != nil {
			t.Fatal(err)
		}
		return v
	}
	a = get()
	if a.Generation != 1 || a.Status.Phase != "" {
		t.Fatalf("create generation/status=%+v", a)
	}
	// Root endpoint must not accept a forged status.
	a.Status.Phase = "forged"
	a.Labels = map[string]string{"stage": "root-update"}
	if err := c.Update(ctx, a); err != nil {
		t.Fatal(err)
	}
	a = get()
	if a.Status.Phase != "" || a.Generation != 1 {
		t.Fatal("root update crossed status boundary")
	}
	// Status endpoint must preserve spec and generation.
	a.Status.Phase = "Ready"
	a.Status.ObservedGeneration = a.Generation
	a.Spec.Image = "forged-spec"
	if os.Getenv("RELIABILITY_MUTANT") == "root_status_write" {
		err = c.Update(ctx, a)
	} else {
		err = c.Status().Update(ctx, a)
	}
	if err != nil {
		t.Fatal(err)
	}
	a = get()
	if a.Status.Phase != "Ready" || a.Spec.Image != "app:v1" || a.Generation != 1 {
		t.Fatalf("status writer contract: %+v", a)
	}
	// Spec update increments generation; it does not advance observedGeneration.
	a.Spec.Image = "app:v2"
	if err := c.Update(ctx, a); err != nil {
		t.Fatal(err)
	}
	a = get()
	if a.Generation != 2 || a.Status.ObservedGeneration != 1 {
		t.Fatalf("generation split: %+v", a)
	}
	stale := a.DeepCopy()
	a.Labels["stage"] = "new-resource-version"
	if err := c.Update(ctx, a); err != nil {
		t.Fatal(err)
	}
	stale.Status.Phase = "stale-writer"
	if err := c.Status().Update(ctx, stale); !apierrors.IsConflict(err) {
		t.Fatalf("stale RV must conflict: %v", err)
	}
	t.Log("INTEGRATION_TESTED owned real API: status isolation, generation 1->2, observedGeneration remains 1, stale resourceVersion rejected")
}
