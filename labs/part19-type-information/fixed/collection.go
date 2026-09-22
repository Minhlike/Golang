package fixed

// Unique returns first occurrences in encounter order.
func Unique[T comparable](values []T) []T {
	seen := make(map[T]struct{}, len(values))
	result := make([]T, 0, len(values))
	for _, value := range values {
		if _, found := seen[value]; found {
			continue
		}
		seen[value] = struct{}{}
		result = append(result, value)
	}
	return result
}

type Set[T comparable] map[T]struct{}

func NewSet[T comparable](values ...T) Set[T] {
	set := make(Set[T], len(values))
	for _, value := range values {
		set[value] = struct{}{}
	}
	return set
}

func (set Set[T]) Has(value T) bool {
	_, found := set[value]
	return found
}

type Batch[E any] []E

func (batch Batch[E]) Map[F any](fn func(E) F) Batch[F] {
	result := make(Batch[F], len(batch))
	for i, value := range batch {
		result[i] = fn(value)
	}
	return result
}
