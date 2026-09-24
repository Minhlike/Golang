package controllers

import (
	"context"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	appsv1alpha1 "example.com/golang-master/part23-controller-runtime-operator/api/v1alpha1"
)

const AppServiceFinalizer = "apps.example.com/finalizer"

// ExternalCleaner defines the contract for cleaning up resources outside Kubernetes (e.g. cloud resources).
type ExternalCleaner interface {
	Cleanup(ctx context.Context, app *appsv1alpha1.AppService) error
}

// AppServiceReconciler reconciles an AppService object.
type AppServiceReconciler struct {
	client.Client
	Scheme          *runtime.Scheme
	ExternalCleaner ExternalCleaner
}

// Reconcile is the core reconciliation loop for AppService resources.
func (r *AppServiceReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	appService := &appsv1alpha1.AppService{}
	if err := r.Get(ctx, req.NamespacedName, appService); err != nil {
		if errors.IsNotFound(err) {
			// Object deleted from etcd; nothing more to do
			return ctrl.Result{}, nil
		}
		return ctrl.Result{}, fmt.Errorf("failed to fetch AppService: %w", err)
	}

	// 1. Finalizer handling: Resource lifecycle deletion gate
	if !appService.DeletionTimestamp.IsZero() {
		if controllerutil.ContainsFinalizer(appService, AppServiceFinalizer) {
			// Perform idempotent external cleanup
			if r.ExternalCleaner != nil {
				if err := r.ExternalCleaner.Cleanup(ctx, appService); err != nil {
					// Return error to trigger rate-limited retry
					return ctrl.Result{}, fmt.Errorf("external cleanup failed: %w", err)
				}
			}
			// Cleanup succeeded; remove finalizer to allow Kubernetes to delete object from etcd
			controllerutil.RemoveFinalizer(appService, AppServiceFinalizer)
			if err := r.Update(ctx, appService); err != nil {
				return ctrl.Result{}, fmt.Errorf("failed to remove finalizer: %w", err)
			}
		}
		return ctrl.Result{}, nil
	}

	// Register finalizer if not present
	if !controllerutil.ContainsFinalizer(appService, AppServiceFinalizer) {
		controllerutil.AddFinalizer(appService, AppServiceFinalizer)
		if err := r.Update(ctx, appService); err != nil {
			return ctrl.Result{}, fmt.Errorf("failed to add finalizer: %w", err)
		}
	}

	// 2. Reconcile Owned Deployment
	deployment := &appsv1.Deployment{}
	depKey := client.ObjectKey{Namespace: appService.Namespace, Name: appService.Name}
	err := r.Get(ctx, depKey, deployment)

	if errors.IsNotFound(err) {
		// Define child deployment with OwnerReference
		newDep := r.buildDesiredDeployment(appService)
		if err := controllerutil.SetControllerReference(appService, newDep, r.Scheme); err != nil {
			return ctrl.Result{}, fmt.Errorf("failed to set controller reference: %w", err)
		}
		if err := r.Create(ctx, newDep); err != nil {
			return ctrl.Result{}, fmt.Errorf("failed to create child deployment: %w", err)
		}
		// Deployment created; requeue to check status
		return ctrl.Result{Requeue: true}, nil
	} else if err != nil {
		return ctrl.Result{}, fmt.Errorf("failed to get child deployment: %w", err)
	}

	// Child deployment exists: check for configuration drift
	drifted := false
	if deployment.Spec.Replicas == nil || *deployment.Spec.Replicas != appService.Spec.Replicas {
		deployment.Spec.Replicas = &appService.Spec.Replicas
		drifted = true
	}
	if len(deployment.Spec.Template.Spec.Containers) > 0 {
		if deployment.Spec.Template.Spec.Containers[0].Image != appService.Spec.Image {
			deployment.Spec.Template.Spec.Containers[0].Image = appService.Spec.Image
			drifted = true
		}
	}

	if drifted {
		if err := r.Update(ctx, deployment); err != nil {
			return ctrl.Result{}, fmt.Errorf("failed to update drifted deployment: %w", err)
		}
	}

	// 3. Reconcile Status Subresource (isolate status from spec)
	var newPhase string
	if deployment.Status.AvailableReplicas >= appService.Spec.Replicas {
		newPhase = "Ready"
	} else {
		newPhase = "Progressing"
	}

	if appService.Status.AvailableReplicas != deployment.Status.AvailableReplicas ||
		appService.Status.Phase != newPhase {
		appService.Status.AvailableReplicas = deployment.Status.AvailableReplicas
		appService.Status.Phase = newPhase
		// Rule: ALWAYS update status via StatusWriter, never mutate spec!
		if err := r.Status().Update(ctx, appService); err != nil {
			return ctrl.Result{}, fmt.Errorf("failed to update AppService status: %w", err)
		}
	}

	return ctrl.Result{}, nil
}

func (r *AppServiceReconciler) buildDesiredDeployment(app *appsv1alpha1.AppService) *appsv1.Deployment {
	labels := map[string]string{
		"app.kubernetes.io/name":       "appservice",
		"app.kubernetes.io/instance":   app.Name,
		"app.kubernetes.io/managed-by": "appservice-operator",
	}

	return &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      app.Name,
			Namespace: app.Namespace,
			Labels:    labels,
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &app.Spec.Replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: labels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: labels,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "app",
							Image: app.Spec.Image,
							Ports: []corev1.ContainerPort{
								{ContainerPort: app.Spec.Port},
							},
						},
					},
				},
			},
		},
	}
}
