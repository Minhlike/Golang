package observer

import (
	"testing"

	appsv1 "k8s.io/api/apps/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func TestDescribeDoesNotInferHealthFromObservedGeneration(t *testing.T) {
	d := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{Generation: 5},
		Status:     appsv1.DeploymentStatus{ObservedGeneration: 5},
	}
	got := Describe(d)
	if got != (Observation{Generation: 5, ObservedGeneration: 5, Desired: 1}) {
		t.Fatalf("Describe() = %#v", got)
	}
	zero := int32(0)
	d.Spec.Replicas = &zero
	d.Status.UpdatedReplicas = 2
	d.Status.AvailableReplicas = 1
	got = Describe(d)
	if got.Desired != 0 || got.Updated != 2 || got.Available != 1 {
		t.Fatalf("zero desired and observed counts were conflated: %#v", got)
	}
}
