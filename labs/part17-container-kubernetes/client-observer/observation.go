package observer

import appsv1 "k8s.io/api/apps/v1"

// Observation is intentionally smaller than a controller status. It is what a
// read-only diagnostic client can say about a Deployment at one observation.
type Observation struct {
	Generation         int64
	ObservedGeneration int64
	Desired            int32
	Updated            int32
	Available          int32
}

func Describe(deployment *appsv1.Deployment) Observation {
	desired := int32(1)
	if deployment.Spec.Replicas != nil {
		desired = *deployment.Spec.Replicas
	}
	return Observation{
		Generation:         deployment.Generation,
		ObservedGeneration: deployment.Status.ObservedGeneration,
		Desired:            desired,
		Updated:            deployment.Status.UpdatedReplicas,
		Available:          deployment.Status.AvailableReplicas,
	}
}
