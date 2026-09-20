package main

import "fmt"

type Service struct {
	Name    string
	Port    int
	Healthy bool
	Retries int
}

type SummarySource interface {
	Summary() string
}

type ProbeRecorder interface {
	Record(bool)
}

type StaticTarget string

func (service Service) Summary() string {
	return fmt.Sprintf("%s healthy=%t retries=%d", service.Name, service.Healthy, service.Retries)
}

func (service *Service) Record(healthy bool) {
	service.Healthy = healthy
	if !healthy {
		service.Retries++
	}
}

func (target StaticTarget) Summary() string {
	return string(target)
}

func renderSummary(source SummarySource) string {
	return "target: " + source.Summary()
}

func markFailed(recorder ProbeRecorder) {
	recorder.Record(false)
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
	fmt.Println(renderSummary(billing))
	markFailed(&billing)
	fmt.Println(billing.Healthy, billing.Retries)

	attempts := map[string]int{"billing": 0}
	count, found := attempts["billing"]
	fmt.Println(count, found)
	_, found = attempts["search"]
	fmt.Println(found)

	services := map[string]Service{"billing": {Name: "billing", Healthy: true}}
	fmt.Println(recordProbe(services, "billing", false), services["billing"].Retries)
}
