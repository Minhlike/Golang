# ==============================================================================
# OPSPROBE DOCKERFILE (MULTI-STAGE DISTROLESS NON-ROOT)
# Vị trí: projects/opsprobe/deploy/Dockerfile
# Trạng thái: Reviewable Containerfile tuân thủ nghiêm ngặt chuẩn bảo mật tối thiểu
# ==============================================================================

# STAGE 1: Build binary thuần Go, không phụ thuộc CGO
FROM golang:1.27.1-alpine AS builder

WORKDIR /build

# Tách riêng lớp cache dependency
COPY go.mod go.sum ./
RUN go mod download

# Sao chép toàn bộ mã nguồn module opsprobe
COPY . .

# Biên dịch tĩnh hoàn toàn: CGO_ENABLED=0, loại bỏ bảng debug và symbol (-s -w)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags="-s -w" -o /build/opsprobe ./cmd/opsprobe

# STAGE 2: Image runtime distroless tối giản, không shell, không package manager
FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /app

# Thư mục chứa dữ liệu SQLite được mount volume ghi được
VOLUME /data

# Sao chép binary từ builder stage
COPY --from=builder /build/opsprobe /app/opsprobe

# Chạy dưới tài khoản không đặc quyền (non-root: nonroot / UID 65532)
USER 65532:65532

EXPOSE 8080

ENTRYPOINT ["/app/opsprobe"]
CMD ["--addr=:8080", "--db=/data/opsprobe.db", "--concurrency=4", "--timeout=3s"]
