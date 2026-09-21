package fixed

import (
	"errors"
	"testing"
)

type Config struct {
	Endpoint string `env:"OPS_ENDPOINT"`
	Token    string `env:"OPS_TOKEN"`
	Retries  int    `env:"OPS_RETRIES"`
	debug    string `env:"OPS_DEBUG"`
}

func TestApplyEnvSetsTaggedExportedStringFields(t *testing.T) {
	config := Config{Token: "keep"}
	err := ApplyEnv(&config, map[string]string{"OPS_ENDPOINT": "https://api.test", "OPS_DEBUG": "true"})
	if err != nil {
		t.Fatalf("ApplyEnv() error = %v", err)
	}
	if config.Endpoint != "https://api.test" {
		t.Fatalf("Endpoint = %q", config.Endpoint)
	}
	if config.Token != "keep" || config.debug != "" {
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
}

func TestApplyEnvRejectsTaggedNonStringField(t *testing.T) {
	config := Config{}
	if err := ApplyEnv(&config, map[string]string{"OPS_RETRIES": "3"}); err == nil {
		t.Fatal("ApplyEnv() accepted a tagged int field")
	}
}
