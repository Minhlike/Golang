package fixed

import (
	"errors"
	"fmt"
	"reflect"
)

var ErrDestination = errors.New("destination must be a non-nil pointer to struct")

func ApplyEnv(dst any, values map[string]string) error {
	value := reflect.ValueOf(dst)
	if value.Kind() != reflect.Pointer || value.IsNil() || value.Elem().Kind() != reflect.Struct {
		return ErrDestination
	}

	target := value.Elem()
	typ := target.Type()
	for i := 0; i < typ.NumField(); i++ {
		field := typ.Field(i)
		name, ok := field.Tag.Lookup("env")
		if !ok || name == "-" || !field.IsExported() {
			continue
		}
		raw, found := values[name]
		if !found {
			continue
		}
		if field.Type.Kind() != reflect.String {
			return fmt.Errorf("env field %s must be string", field.Name)
		}
		fieldValue := target.Field(i)
		if !fieldValue.CanSet() {
			return fmt.Errorf("env field %s cannot be set", field.Name)
		}
		fieldValue.SetString(raw)
	}
	return nil
}
