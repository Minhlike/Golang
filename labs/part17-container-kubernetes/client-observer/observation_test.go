package observer

import (
	"testing"

	appsv1 "k8s.io/api/apps/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func TestDescribeKeepsSpecAndStatusSeparate(t *testing.T) {
	replicas := int32(3)
	deployment := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{Generation: 8},
		Spec:       appsv1.DeploymentSpec{Replicas: &replicas},
		Status: appsv1.DeploymentStatus{
			ObservedGeneration: 7,
			UpdatedReplicas:    2,
			AvailableReplicas:  1,
		},
	}
	got := Describe(deployment)
	if got.Desired != 3 || got.ObservedGeneration != 7 || got.Available != 1 {
		t.Fatalf("Describe() = %#v", got)
	}
}
