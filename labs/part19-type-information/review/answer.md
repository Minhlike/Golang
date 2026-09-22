# Đáp án review

`T any` không cho `Load` một operation để biến bytes thành `T`; nó chỉ trì hoãn
câu hỏi decode. `source string` cũng không nói caller sở hữu file, URL, byte
stream hay config value nào. Generic ở đây che format policy thay vì mô tả
contract.

Một boundary nhỏ hơn bắt đầu bằng input thật, chẳng hạn `func DecodeJSON[T
any](r io.Reader) (T, error)` khi JSON là format đã chọn và caller sở hữu reader
lifecycle, hoặc `func ReadConfig(path string) ([]byte, error)` nếu package chỉ
đọc bytes. Hai API có thể nằm ở package khác nhau. Generic chỉ có ích ở API
decode sau khi format và error policy đã được nói rõ.
