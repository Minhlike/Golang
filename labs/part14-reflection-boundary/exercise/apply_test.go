//go:build exercise

package exercise

import (
	"errors"
	"testing"
)

type Config struct {
	Endpoint string `env:"OPS_ENDPOINT"`
	Token    string `env:"OPS_TOKEN"`
	Ignored  string `env:"-"`
}

type nonStringConfig struct {
	Retries int `env:"OPS_RETRIES"`
}

type Token string

type namedStringConfig struct {
	Token Token `env:"OPS_TOKEN"`
}

type unexportedTaggedConfig struct {
	Endpoint string `env:"OPS_ENDPOINT"`
	secret   string `env:"OPS_SECRET"`
}

func TestApplyEnvSetsTaggedExportedStringFields(t *testing.T) {
	config := Config{Token: "keep"}
	err := ApplyEnv(&config, map[string]string{"OPS_ENDPOINT": "https://api.test"})
	if err != nil {
		t.Fatalf("ApplyEnv() error = %v", err)
	}
	if config.Endpoint != "https://api.test" {
		t.Fatalf("Endpoint = %q", config.Endpoint)
	}
	if config.Token != "keep" {
		t.Fatalf("unexpected config mutation: %#v", config)
	}
}

func TestApplyEnvRejectsValueAndNilPointer(t *testing.T) {
	if err := ApplyEnv(Config{}, nil); !errors.Is(err, ErrDestination) {
		t.Fatalf("value error = %v, want ErrDestination", err)
	}
	var config *Config
	if err := ApplyEnv(config, nil); !errors.Is(err, ErrDestination) {
		t.Fatalf("nil pointer error = %v, want ErrDestination", err)
	}
	if err := ApplyEnv(nil, nil); !errors.Is(err, ErrDestination) {
		t.Fatalf("untyped nil error = %v, want ErrDestination", err)
	}
}

func TestApplyEnvRejectsTaggedNonStringField(t *testing.T) {
	config := nonStringConfig{}
	if err := ApplyEnv(&config, map[string]string{"OPS_RETRIES": "3"}); !errors.Is(err, ErrSchema) {
		t.Fatalf("ApplyEnv() error = %v, want ErrSchema", err)
	}
}

func TestApplyEnvRejectsNamedStringType(t *testing.T) {
	config := namedStringConfig{Token: "keep"}
	err := ApplyEnv(&config, map[string]string{"OPS_TOKEN": "replace"})
	if !errors.Is(err, ErrSchema) {
		t.Fatalf("ApplyEnv() error = %v, want ErrSchema", err)
	}
	if config.Token != "keep" {
		t.Fatalf("named string field changed to %q", config.Token)
	}
}

func TestApplyEnvRejectsTaggedUnexportedField(t *testing.T) {
	config := unexportedTaggedConfig{Endpoint: "keep", secret: "private"}
	err := ApplyEnv(&config, map[string]string{
		"OPS_ENDPOINT": "replace",
		"OPS_SECRET":   "leak",
	})
	if !errors.Is(err, ErrSchema) {
		t.Fatalf("ApplyEnv() error = %v, want ErrSchema", err)
	}
	if config.Endpoint != "keep" || config.secret != "private" {
		t.Fatalf("schema failure partially mutated %#v", config)
	}
}

func TestApplyEnvDoesNotPartiallyMutateOnSchemaError(t *testing.T) {
	config := struct {
		Endpoint string `env:"OPS_ENDPOINT"`
		Retries  int    `env:"OPS_RETRIES"`
	}{Endpoint: "keep-endpoint"}
	err := ApplyEnv(&config, map[string]string{
		"OPS_ENDPOINT": "replace-endpoint",
		"OPS_TOKEN":    "replace-token",
		"OPS_RETRIES":  "3",
	})
	if !errors.Is(err, ErrSchema) {
		t.Fatalf("ApplyEnv() error = %v, want ErrSchema", err)
	}
	if config.Endpoint != "keep-endpoint" {
		t.Fatalf("schema failure partially mutated %#v", config)
	}
}

func TestApplyEnvIgnoresOptOutAndMissingValue(t *testing.T) {
	config := Config{Token: "keep-token", Ignored: "keep-ignored"}
	err := ApplyEnv(&config, map[string]string{
		"OPS_ENDPOINT": "https://api.test",
		"-":            "must-not-apply",
	})
	if err != nil {
		t.Fatalf("ApplyEnv() error = %v", err)
	}
	if config.Endpoint != "https://api.test" || config.Token != "keep-token" || config.Ignored != "keep-ignored" {
		t.Fatalf("unexpected config mutation: %#v", config)
	}
}
