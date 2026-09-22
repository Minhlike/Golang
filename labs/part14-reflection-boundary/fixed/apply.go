package fixed

import (
	"errors"
	"fmt"
	"reflect"
)

var (
	ErrDestination = errors.New("destination must be a non-nil pointer to struct")
	ErrSchema      = errors.New("invalid env schema")
)

type assignment struct {
	field reflect.Value
	raw   string
}

func schemaError(field, rule string) error {
	return fmt.Errorf(
		"%w: env field %s %s",
		ErrSchema,
		field,
		rule,
	)
}

func ApplyEnv(dst any, values map[string]string) error {
	value := reflect.ValueOf(dst)
	if !value.IsValid() ||
		value.Kind() != reflect.Pointer ||
		value.IsNil() {
		return ErrDestination
	}

	target := value.Elem()
	if target.Kind() != reflect.Struct {
		return ErrDestination
	}
	typ := target.Type()
	stringType := reflect.TypeFor[string]()
	assignments := make([]assignment, 0, typ.NumField())
	for i := 0; i < typ.NumField(); i++ {
		field := typ.Field(i)
		name, ok := field.Tag.Lookup("env")
		if !ok || name == "-" {
			continue
		}
		if !field.IsExported() {
			return schemaError(field.Name, "is unexported")
		}
		if field.Type != stringType {
			return schemaError(field.Name, "must be string")
		}
		fieldValue := target.Field(i)
		if !fieldValue.CanSet() {
			return schemaError(field.Name, "cannot be set")
		}
		if raw, found := values[name]; found {
			assignments = append(assignments, assignment{
				field: fieldValue,
				raw:   raw,
			})
		}
	}
	for _, assignment := range assignments {
		assignment.field.SetString(assignment.raw)
	}
	return nil
}
