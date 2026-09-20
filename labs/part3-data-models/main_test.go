package main

import "testing"

var _ SummarySource = Service{}
var _ SummarySource = (*Service)(nil)
var _ SummarySource = StaticTarget("")
var _ ProbeRecorder = (*Service)(nil)

func TestRecordFailureMutatesPointee(t *testing.T) {
	billing := Service{Name: "billing", Healthy: true}
	recordFailure(&billing)

	if billing.Healthy || billing.Retries != 1 {
		t.Fatalf("billing = %+v, want Healthy=false and Retries=1", billing)
	}
}

func TestFailedCopyLeavesInputUntouched(t *testing.T) {
	billing := Service{Name: "billing", Healthy: true}
	failed := failedCopy(billing)

	if !billing.Healthy || billing.Retries != 0 {
		t.Fatalf("input changed: %+v", billing)
	}
	if failed.Healthy || failed.Retries != 1 {
		t.Fatalf("result = %+v, want Healthy=false and Retries=1", failed)
	}
}

func TestCommaOKDistinguishesZeroFromMissing(t *testing.T) {
	attempts := map[string]int{"billing": 0}

	count, found := attempts["billing"]
	if count != 0 || !found {
		t.Fatalf("billing lookup = (%d, %t), want (0, true)", count, found)
	}
	count, found = attempts["search"]
	if count != 0 || found {
		t.Fatalf("search lookup = (%d, %t), want (0, false)", count, found)
	}
}

func TestRecordProbeUpdatesExistingMapEntry(t *testing.T) {
	services := map[string]Service{
		"billing": {Name: "billing", Healthy: true},
	}

	if !recordProbe(services, "billing", false) {
		t.Fatal("recordProbe reported a known service as missing")
	}
	if got := services["billing"]; got.Healthy || got.Retries != 1 {
		t.Fatalf("billing = %+v, want Healthy=false and Retries=1", got)
	}
	if recordProbe(services, "search", false) {
		t.Fatal("recordProbe reported a missing service as present")
	}
}

func TestMethodReceiverContracts(t *testing.T) {
	billing := Service{Name: "billing", Healthy: true}

	if got := renderSummary(billing); got != "target: billing healthy=true retries=0" {
		t.Fatalf("renderSummary(Service) = %q", got)
	}
	if got := renderSummary(StaticTarget("maintenance")); got != "target: maintenance" {
		t.Fatalf("renderSummary(StaticTarget) = %q", got)
	}

	markFailed(&billing)
	if billing.Healthy || billing.Retries != 1 {
		t.Fatalf("billing = %+v, want Healthy=false and Retries=1", billing)
	}
}
