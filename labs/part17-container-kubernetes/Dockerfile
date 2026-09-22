# Build with context labs/part16-real-signals, not repository root.
FROM golang:1.27.1 AS build
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -o /out/probe-api ./cmd/probe-api

# The final image has the binary only. It deliberately has no package manager
# or shell; debug with an ephemeral toolbox, not by widening this runtime image.
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/probe-api /probe-api
USER 65532:65532
ENTRYPOINT ["/probe-api"]
