package main

import "fmt"

type Service struct {
	Name    string
	Port    int
	Healthy bool
	Retries int
}

func recordFailure(service *Service) {
	service.Healthy = false
	service.Retries++
}

func failedCopy(service Service) Service {
	service.Healthy = false
	service.Retries++
	return service
}

func recordProbe(registry map[string]Service, name string, healthy bool) bool {
	service, found := registry[name]
	if !found {
		return false
	}

	service.Healthy = healthy
	if !healthy {
		service.Retries++
	}
	registry[name] = service
	return true
}

func main() {
	billing := Service{Name: "billing", Port: 8080, Healthy: true}
	recordFailure(&billing)
	fmt.Println(billing.Healthy, billing.Retries)

	attempts := map[string]int{"billing": 0}
	count, found := attempts["billing"]
	fmt.Println(count, found)
	_, found = attempts["search"]
	fmt.Println(found)

	services := map[string]Service{"billing": {Name: "billing", Healthy: true}}
	fmt.Println(recordProbe(services, "billing", false), services["billing"].Retries)
}
