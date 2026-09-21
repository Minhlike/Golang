//go:build exercise

package exercise

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCreateCheckAcceptsValidatedTarget(t *testing.T) {
	store := &fakeStore{}
	handler := NewHandler(store)
	req := httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewBufferString(`{"target":"https://api.test/health"}`))
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	result := resp.Result()
	defer result.Body.Close()
	if result.StatusCode != http.StatusCreated {
		t.Fatalf("status = %d, want %d", result.StatusCode, http.StatusCreated)
	}
	if len(store.created) != 1 || store.created[0].Target != "https://api.test/health" {
		t.Fatalf("store got %#v", store.created)
	}
}

func TestCreateCheckRejectsUnknownFieldWithoutCallingStore(t *testing.T) {
	store := &fakeStore{}
	handler := NewHandler(store)
	req := httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewBufferString(`{"target":"https://api.test","debug":true}`))
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	if resp.Result().StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d", resp.Result().StatusCode, http.StatusBadRequest)
	}
	if len(store.created) != 0 {
		t.Fatalf("store was called with %#v", store.created)
	}
}

func TestCreateCheckRejectsMethod(t *testing.T) {
	handler := NewHandler(&fakeStore{})
	req := httptest.NewRequest(http.MethodGet, "/v1/checks", nil)
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	if resp.Result().StatusCode != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d, want %d", resp.Result().StatusCode, http.StatusMethodNotAllowed)
	}
}

func TestCreateCheckRejectsUnsafeScheme(t *testing.T) {
	store := &fakeStore{}
	handler := NewHandler(store)
	req := httptest.NewRequest(http.MethodPost, "/v1/checks", bytes.NewBufferString(`{"target":"file:///etc/passwd"}`))
	resp := httptest.NewRecorder()

	handler.ServeHTTP(resp, req)
	if resp.Result().StatusCode != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d", resp.Result().StatusCode, http.StatusBadRequest)
	}
}

type fakeStore struct{ created []Check }

func (s *fakeStore) Create(_ context.Context, check Check) (Check, error) {
	s.created = append(s.created, check)
	return check, nil
}

func decodeBody(t *testing.T, recorder *httptest.ResponseRecorder) map[string]any {
	t.Helper()
	var value map[string]any
	if err := json.NewDecoder(recorder.Result().Body).Decode(&value); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	return value
}
