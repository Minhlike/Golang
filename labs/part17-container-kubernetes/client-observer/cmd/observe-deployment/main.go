package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"example.com/golang-master/part17-client-observer"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

func main() {
	namespace := flag.String("namespace", "go-book", "Kubernetes namespace")
	name := flag.String("name", "probe-api", "Deployment name")
	kubeconfig := flag.String("kubeconfig", defaultKubeconfig(), "path to kubeconfig")
	flag.Parse()

	config, err := clientcmd.BuildConfigFromFlags("", *kubeconfig)
	if err != nil {
		fail("load kubeconfig", err)
	}
	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		fail("create client", err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	deployments := client.AppsV1().Deployments(*namespace)
	deployment, err := deployments.Get(ctx, *name, metav1.GetOptions{})
	if err != nil {
		fail("get deployment", err)
	}
	printObservation("get", observer.Describe(deployment))

	watch, err := deployments.Watch(ctx, metav1.ListOptions{
		FieldSelector: fields.OneTermEqualSelector("metadata.name", *name).String(),
	})
	if err != nil {
		fail("watch deployment", err)
	}
	defer watch.Stop()
	select {
	case event, ok := <-watch.ResultChan():
		if !ok {
			fmt.Fprintln(os.Stderr, "watch ended before an event; relist before retrying")
			return
		}
		fmt.Printf("watch event: %s\n", event.Type)
	case <-ctx.Done():
		fmt.Fprintln(os.Stderr, "no watch event within 15s; this is not a failure of the Deployment")
	}
}

func defaultKubeconfig() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".kube", "config")
}

func printObservation(source string, observation observer.Observation) {
	fmt.Printf(
		"%s: generation=%d observed=%d desired=%d updated=%d available=%d\n",
		source,
		observation.Generation,
		observation.ObservedGeneration,
		observation.Desired,
		observation.Updated,
		observation.Available,
	)
}

func fail(action string, err error) {
	fmt.Fprintf(os.Stderr, "%s: %v\n", action, err)
	os.Exit(1)
}
