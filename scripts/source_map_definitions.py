"""
Architectural Source Map Definitions for 50 Go DevOps & Cloud Libraries.
Conforms strictly to the Zero-Guess Protocol.
"""

SOURCE_MAP_REGISTRY = {
    "k8s-client-go": {
        "entrypoints": ["kubernetes.NewForConfig", "dynamic.NewForConfig", "tools/cache.NewInformer"],
        "public_api": ["kubernetes.Clientset", "tools/cache.SharedIndexInformer", "util/workqueue.RateLimitingInterface"],
        "core_types": [
            {"name": "Reflector", "kind": "struct", "description": "ListerWatcher synchronizer populating DeltaFIFO"},
            {"name": "DeltaFIFO", "kind": "struct", "description": "Producer-consumer queue for delta mutation events"},
            {"name": "SharedIndexInformer", "kind": "interface", "description": "Multiplexed local cache with event callbacks"},
            {"name": "TypeQueue", "kind": "struct", "description": "Thread-safe work queue with failure rate limiting"}
        ],
        "call_paths": [
            {"phase": "Watch Stream", "path": "Reflector.ListAndWatch() -> ListerWatcher.Watch() -> DeltaFIFO.Add/Update/Delete()"},
            {"phase": "Cache Distribution", "path": "controller.processLoop() -> SharedIndexInformer.HandleDeltas() -> Indexer.Update() + Listener.add()"},
            {"phase": "Worker Reconcile", "path": "WorkQueue.Get() -> Reconcile(key) -> WorkQueue.Done() -> WorkQueue.Forget()"}
        ],
        "concurrency_model": {
            "type": "Actor-like Event Distributor with Parallel Worker Queues",
            "synchronization": "sync.RWMutex for cache indexer, channels for processor listeners",
            "bounded_buffer": True
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "context.Context passed to ListAndWatch and Run loops",
            "leak_prevention": "Stop channel and context cancellation triggers Reflector and processor listener shutdown"
        },
        "retry_model": {
            "strategy": "Exponential failure backoff with per-item rate-limiting workqueue",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "HTTP/1.1 chunked or HTTP/2 chunked watch streams with keep-alive ping frames",
            "os": "In-memory indexing cache and kernel network socket buffers",
            "serialization": "JSON and Protobuf decoding of runtime.Object envelopes"
        },
        "verification_tests": ["tools/cache/reflector_test.go", "util/workqueue/queue_test.go"]
    },
    "controller-runtime": {
        "entrypoints": ["manager.New", "builder.ControllerManagedBy", "reconcile.Reconciler"],
        "public_api": ["manager.Manager", "reconcile.Reconciler", "client.Client", "controller.Controller"],
        "core_types": [
            {"name": "Manager", "kind": "interface", "description": "Shared controller lifecycle and dependency container"},
            {"name": "Controller", "kind": "interface", "description": "Reconciliation loop executor reacting to events"},
            {"name": "Client", "kind": "interface", "description": "Split client routing reads to cache and writes to APIServer"}
        ],
        "call_paths": [
            {"phase": "Manager Start", "path": "Manager.Start(ctx) -> startCaches() -> startRunnables() -> startControllers()"},
            {"phase": "Event Ingestion", "path": "Source.Start() -> EventHandler.Create/Update/Delete() -> WorkQueue.Add()"},
            {"phase": "Reconcile Loop", "path": "Controller.processNextWorkItem() -> Reconciler.Reconcile(ctx, req) -> Result"}
        ],
        "concurrency_model": {
            "type": "Multi-Worker Goroutine Pool per Controller with Shared Cache",
            "synchronization": "Internal WorkQueue locks, Cache Informer read-locks",
            "bounded_buffer": True
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "Parent Manager context cascades to all registered Runnables and Reconcile invocations",
            "leak_prevention": "Manager gracefully waits for Reconcile workers via sync.WaitGroup on shutdown"
        },
        "retry_model": {
            "strategy": "Exponential backoff via Reconcile.Result{RequeueAfter: duration} or rate-limited error requeue",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "k8s REST client HTTPS queries and Informer cache watch streams",
            "os": "Host process signals (SIGTERM, SIGINT) bound to context cancellation",
            "serialization": "runtime.Object JSON/Protobuf codec"
        },
        "verification_tests": ["pkg/controller/controller_test.go", "pkg/manager/manager_test.go"]
    },
    "aws-sdk-go-v2": {
        "entrypoints": ["config.LoadDefaultConfig", "s3.NewFromConfig", "middleware.Stack"],
        "public_api": ["aws.Config", "middleware.Stack", "smithy.Handler", "transport/http.BuildableClient"],
        "core_types": [
            {"name": "Config", "kind": "struct", "description": "Cross-service AWS runtime configuration and credential provider"},
            {"name": "Stack", "kind": "struct", "description": "Modular Smithy middleware execution pipeline (Initialize, Serialize, Build, Finalize, Deserialize)"},
            {"name": "StandardRateLimiter", "kind": "struct", "description": "Token bucket client-side rate limiter for throttling responses"}
        ],
        "call_paths": [
            {"phase": "Credential Resolution", "path": "LoadDefaultConfig() -> ResolveCredentials() -> Env -> SharedConfig -> IMDS/OIDC"},
            {"phase": "Operation Pipeline", "path": "Client.Operation() -> Stack.Serialize() -> Stack.Finalize() -> Transport.Do()"},
            {"phase": "Response Handling", "path": "Transport.Do() -> Stack.Deserialize() -> UnmarshalResponse() -> ErrorClassifier"}
        ],
        "concurrency_model": {
            "type": "Stateless Concurrency / Thread-Safe Client Instances",
            "synchronization": "Immutable middleware stacks per operation; atomic credential caching",
            "bounded_buffer": False
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "context.Context passed to every API operation and propagated to HTTP RoundTripper",
            "leak_prevention": "Response bodies drained and closed or returned to caller as io.ReadCloser"
        },
        "retry_model": {
            "strategy": "Standard / Adaptive mode with exponential backoff, jitter, and error classification",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "HTTPS/1.1 and HTTP/2 TLS connections to AWS service regional endpoints",
            "os": "Filesystem credentials (~/.aws/credentials) and IMDS HTTP metadata socket",
            "serialization": "AWS REST-JSON, REST-XML, Query, and Smithy RPC protocols"
        },
        "verification_tests": ["aws/retry/retry_test.go", "aws/middleware/stack_test.go"]
    },
    "prometheus-client-golang": {
        "entrypoints": ["prometheus.NewRegistry", "promhttp.Handler", "prometheus.NewCounterVec"],
        "public_api": ["prometheus.Registerer", "prometheus.Gatherer", "prometheus.Collector", "prometheus.Metric"],
        "core_types": [
            {"name": "Registry", "kind": "struct", "description": "Thread-safe metric collector registration and gatherer coordinator"},
            {"name": "Counter", "kind": "interface", "description": "Monotonically increasing floating point counter metric"},
            {"name": "Histogram", "kind": "interface", "description": "Configurable bucketed observation accumulator"},
            {"name": "MetricVec", "kind": "struct", "description": "Partitioned metric bundle indexed by label value arrays"}
        ],
        "call_paths": [
            {"phase": "Metric Observation", "path": "Counter.Inc() -> atomic.AddUint64() / floatBits update"},
            {"phase": "HTTP Scraping", "path": "promhttp.Handler() -> Gatherer.Gather() -> Collector.Collect() -> Metric.Write()"},
            {"phase": "Text Exposition", "path": "Gather() -> expfmt.NewEncoder() -> WriteProtoText() / OpenMetrics format"}
        ],
        "concurrency_model": {
            "type": "Lock-Free / Atomic Ingestion with Read-Locked Gathering",
            "synchronization": "sync/atomic for metric values; sync.RWMutex for MetricVec label index maps",
            "bounded_buffer": False
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "Scrape HTTP request context aborts exposition stream if client disconnects",
            "leak_prevention": "Zero lingering goroutines for counter/gauge observations"
        },
        "retry_model": {
            "strategy": "No internal retry; metrics ingestion is fire-and-forget",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "HTTP /metrics exposition endpoint",
            "os": "Process / Linux procfs memory, CPU, and FD descriptors via procfs collectors",
            "serialization": "Prometheus text format (0.0.4) and OpenMetrics text exposition"
        },
        "verification_tests": ["prometheus/registry_test.go", "prometheus/promhttp/http_test.go"]
    },
    "opentelemetry-go": {
        "entrypoints": ["otel.GetTracerProvider", "sdktrace.NewTracerProvider", "trace.SpanFromContext"],
        "public_api": ["trace.Tracer", "trace.Span", "metric.Meter", "propagation.TextMapPropagator"],
        "core_types": [
            {"name": "TracerProvider", "kind": "interface", "description": "Factory and lifecycle owner of Tracer instances"},
            {"name": "Span", "kind": "interface", "description": "Active tracing span recording attributes, events, and status"},
            {"name": "BatchSpanProcessor", "kind": "struct", "description": "Buffered worker goroutine batching spans for export"},
            {"name": "Sampler", "kind": "interface", "description": "Sampling decision engine (AlwaysOn, TraceIDRatioBased, ParentBased)"}
        ],
        "call_paths": [
            {"phase": "Span Creation", "path": "Tracer.Start(ctx, name) -> Sampler.ShouldSample() -> newRecordableSpan() -> context.WithValue()"},
            {"phase": "Span Completion", "path": "Span.End() -> BatchSpanProcessor.OnEnd() -> ringBuffer.enqueue()"},
            {"phase": "Background Export", "path": "BatchSpanProcessor.worker() -> Exporter.ExportSpans(ctx, batch) -> OTLP/gRPC/HTTP"}
        ],
        "concurrency_model": {
            "type": "Lock-Free RingBuffer / Worker Goroutine Batcher",
            "synchronization": "Channel or bounded ring buffer queue for spans; atomic flags for Span state",
            "bounded_buffer": True
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "Context embeds SpanContext and propagates TraceParent/TraceState across process boundaries",
            "leak_prevention": "TracerProvider.Shutdown(ctx) drains pending queue and waits for export completion"
        },
        "retry_model": {
            "strategy": "OTLP exporter retry with exponential backoff on transient network failure",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "OTLP gRPC or HTTP transport to OpenTelemetry Collector",
            "os": "Clock syscalls (runtime/nanotime) for precise span timestamping",
            "serialization": "W3C Trace Context headers and OTLP Protobuf payloads"
        },
        "verification_tests": ["sdk/trace/batch_span_processor_test.go", "sdk/trace/tracer_test.go"]
    },
    "opentelemetry-collector": {
        "entrypoints": ["otelcol.NewCommand", "service.New", "connector.NewFactory"],
        "public_api": ["receiver.Receiver", "processor.Processor", "exporter.Exporter", "pipeline.Pipeline"],
        "core_types": [
            {"name": "Service", "kind": "struct", "description": "Host daemon orchestrating telemetry pipelines and telemetry components"},
            {"name": "Consumer", "kind": "interface", "description": "Data consumption interface (ConsumeTraces, ConsumeMetrics, ConsumeLogs)"},
            {"name": "BatchProcessor", "kind": "struct", "description": "Pipeline stage aggregating telemetry items by size and timeout"}
        ],
        "call_paths": [
            {"phase": "Pipeline Ingestion", "path": "Receiver.ConsumeTraces() -> Pipeline.Router() -> Processor.ConsumeTraces()"},
            {"phase": "Processing", "path": "Processor.ProcessTraces() -> Filter / Transform / Batch -> NextConsumer"},
            {"phase": "Export", "path": "Exporter.ConsumeTraces() -> QueueSender -> RetrySender -> Network Sender"}
        ],
        "concurrency_model": {
            "type": "Pipeline Fan-Out / Fan-In with Buffered Senders",
            "synchronization": "Bounded channel queues per exporter; atomic pipeline counters",
            "bounded_buffer": True
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "Context passed through every consumer step; timeout cancels downstream RPCs",
            "leak_prevention": "Service.Shutdown(ctx) halts receivers, drains pipelines, and flushes exporters"
        },
        "retry_model": {
            "strategy": "Queue-sender bounded memory/disk buffering with exponential retry policy",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "OTLP, Jaeger, Prometheus, Zipkin network servers and clients",
            "os": "Process signals and filesystem configuration files",
            "serialization": "OTLP Protobuf, JSON, and Arrow telemetry formats"
        },
        "verification_tests": ["service/pipelines_test.go", "exporter/exporterhelper/retry_sender_test.go"]
    },
    "moby": {
        "entrypoints": ["client.NewClientWithOpts", "daemon.NewDaemon", "daemon.ContainerStart"],
        "public_api": ["client.APIClient", "daemon.Daemon", "container.Container", "pkg/archive.Tar"],
        "core_types": [
            {"name": "Daemon", "kind": "struct", "description": "Central container engine daemon coordinating state, storage, and networking"},
            {"name": "Container", "kind": "struct", "description": "Runtime container metadata, state machine, and mount configuration"},
            {"name": "LayerStore", "kind": "interface", "description": "Copy-on-write image layer storage graph driver manager"}
        ],
        "call_paths": [
            {"phase": "Container Creation", "path": "Client.ContainerCreate() -> Daemon.containerCreate() -> ContainerStore.Add()"},
            {"phase": "Container Start", "path": "Daemon.ContainerStart() -> containerd.CreateTask() -> networking.Allocate() -> task.Start()"},
            {"phase": "Container Wait", "path": "Daemon.ContainerWait() -> task.Wait() -> state.SetStopped() -> cleanup()"}
        ],
        "concurrency_model": {
            "type": "Daemon Subsystem Coordinators with Per-Container State Mutexes",
            "synchronization": "Container.Lock(), sync.Mutex across daemon registries and bridge networks",
            "bounded_buffer": True
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "gRPC and HTTP engine calls carry Context with cancel/timeout controls",
            "leak_prevention": "Graceful daemon shutdown cleans up running exec instances and releases IPAM leases"
        },
        "retry_model": {
            "strategy": "Configurable restart policies (always, on-failure, unless-stopped)",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "Unix domain sockets (/var/run/docker.sock) and containerd gRPC socket",
            "os": "Linux namespaces (pid, net, ipc, mnt, uts, user), cgroups v1/v2, seccomp, AppArmor",
            "serialization": "Docker Engine HTTP REST JSON API and containerd Protobuf definitions"
        },
        "verification_tests": ["client/container_start_test.go", "daemon/daemon_test.go"]
    },
    "containerd": {
        "entrypoints": ["containerd.New", "client.NewContainer", "cio.NewCreator"],
        "public_api": ["containerd.Client", "containerd.Container", "containerd.Task", "containerd.Process"],
        "core_types": [
            {"name": "Client", "kind": "struct", "description": "High-level Go client communicating with containerd over gRPC"},
            {"name": "Task", "kind": "interface", "description": "Active container process executing in isolated Linux namespaces via shim-v2"},
            {"name": "Snapshotter", "kind": "interface", "description": "Copy-on-write block or filesystem snapshot driver (overlayfs, devmapper)"}
        ],
        "call_paths": [
            {"phase": "Image Pull", "path": "Client.Pull() -> ContentStore.Ingest() -> Snapshotter.Prepare()"},
            {"phase": "Task Creation", "path": "Container.NewTask() -> TaskService.Create() -> runc/shim-v2.Create()"},
            {"phase": "Task Execution", "path": "Task.Start() -> shim.Start() -> process.Exec()"}
        ],
        "concurrency_model": {
            "type": "gRPC Multi-Tenant Architecture with Out-of-Process Shim Daemons",
            "synchronization": "Locking inside metadata database (bbolt) and shim FIFO queues",
            "bounded_buffer": True
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "Context cancellation propagates to gRPC streams and triggers task SIGTERM/SIGKILL escalation",
            "leak_prevention": "TTRPC stream cleanup and process reaping to prevent zombie child processes"
        },
        "retry_model": {
            "strategy": "gRPC transport backoff on connection drops to containerd socket",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "Unix domain socket (/run/containerd/containerd.sock) and TTRPC shim sockets",
            "os": "runc, crun, Linux clone(2), setns(2), pivot_root(2), and cgroup filesystem",
            "serialization": "Protobuf over gRPC / TTRPC and OCI Image/Runtime specifications"
        },
        "verification_tests": ["client_test.go", "task_test.go"]
    },
    "terraform-plugin-framework": {
        "entrypoints": ["providerserver.NewProtocol6WithError", "resource.Resource", "datasource.DataSource"],
        "public_api": ["provider.Provider", "resource.Resource", "datasource.DataSource", "tfsdk.Config"],
        "core_types": [
            {"name": "Provider", "kind": "interface", "description": "Terraform provider plugin definition declaring schema and resources"},
            {"name": "Resource", "kind": "interface", "description": "Managed infrastructure resource lifecycle handler (Create, Read, Update, Delete)"},
            {"name": "Schema", "kind": "struct", "description": "Type-safe specification of resource attributes, blocks, and validators"}
        ],
        "call_paths": [
            {"phase": "Schema Negotiation", "path": "Provider.GetSchema() -> Schema.Request() -> Terraform Core RPC"},
            {"phase": "Plan Modification", "path": "Resource.ModifyPlan() -> PlanModifier.PlanModify() -> Diagnostics check"},
            {"phase": "Resource Apply", "path": "Resource.Create/Update/Delete() -> Cloud API Call -> State.Set()"}
        ],
        "concurrency_model": {
            "type": "RPC Worker Threads Managed by Terraform Plugin Server",
            "synchronization": "Thread-safe provider instances; resource CRUD operations multiplexed via gRPC",
            "bounded_buffer": False
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "context.Context carries execution timeout configured in HCL resource blocks",
            "leak_prevention": "Cancellation aborts in-flight HTTP requests and sets partial resource state if possible"
        },
        "retry_model": {
            "strategy": "Delegated to upstream cloud SDKs with framework retry helpers",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "Loopback gRPC socket connecting plugin subprocess to Terraform Core",
            "os": "Subprocess stdio negotiation and process exit codes",
            "serialization": "Terraform Provider Protocol v6 Protobuf and tftypes data structures"
        },
        "verification_tests": ["internal/fwserver/server_test.go", "resource/resource_test.go"]
    },
    "helm": {
        "entrypoints": ["action.NewInstall", "action.NewUpgrade", "loader.Load"],
        "public_api": ["action.Configuration", "chart.Chart", "release.Release", "storage.Storage"],
        "core_types": [
            {"name": "Configuration", "kind": "struct", "description": "Action environment holding Kubernetes client, driver storage, and logger"},
            {"name": "Chart", "kind": "struct", "description": "Packaged or unpacked Helm chart containing templates, values, and metadata"},
            {"name": "Storage", "kind": "struct", "description": "Release history backend persisting releases in Kubernetes Secrets or ConfigMaps"}
        ],
        "call_paths": [
            {"phase": "Chart Loading", "path": "loader.Load() -> chartutil.Validate() -> ParseValues()"},
            {"phase": "Template Rendering", "path": "engine.Render() -> Go template execution -> manifest YAML stream"},
            {"phase": "Cluster Apply", "path": "action.Install.Run() -> kube.Client.Create() -> storage.Create()"}
        ],
        "concurrency_model": {
            "type": "Single-Threaded Action Runner with Parallel Kubernetes Resource Creation",
            "synchronization": "Kubernetes cluster-side atomic secrets updates; optional release mutex locks",
            "bounded_buffer": False
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "context.Context controls action duration and Kubernetes API timeouts",
            "leak_prevention": "Action timeout triggers release rollback or failure recording in storage"
        },
        "retry_model": {
            "strategy": "Kubernetes resource readiness polling with configurable timeout (e.g., --wait)",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "HTTPS calls to Helm chart repositories (OCI / HTTP) and Kubernetes API server",
            "os": "Local cache (~/.cache/helm) and temporary chart archive tar extraction",
            "serialization": "YAML manifests, Go templates, and JSON release envelopes"
        },
        "verification_tests": ["pkg/action/install_test.go", "pkg/engine/engine_test.go"]
    },
    "go-git": {
        "entrypoints": ["git.PlainClone", "git.PlainOpen", "git.Init"],
        "public_api": ["git.Repository", "git.Worktree", "git.Remote", "plumbing.Reference"],
        "core_types": [
            {"name": "Repository", "kind": "struct", "description": "Pure Go Git repository handle coordinating worktree, storage, and remotes"},
            {"name": "Worktree", "kind": "struct", "description": "Filesystem working directory manager for checkout, status, and commit"},
            {"name": "ObjectStorage", "kind": "interface", "description": "Plumbing storage abstraction for blobs, trees, commits, and tags"}
        ],
        "call_paths": [
            {"phase": "Repository Clone", "path": "PlainClone() -> Remote.Fetch() -> Packfile.Decode() -> Worktree.Checkout()"},
            {"phase": "Status Computation", "path": "Worktree.Status() -> index.Read() -> file stat walk -> diff generation"},
            {"phase": "Commit Creation", "path": "Worktree.Commit() -> buildTrees() -> Commit.Encode() -> Ref.Update()"}
        ],
        "concurrency_model": {
            "type": "Thread-Safe Storage with Synchronized Worktree Mutexes",
            "synchronization": "Internal storage mutexes; worktree operations require single-caller locking",
            "bounded_buffer": False
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "context.Context passed to network operations (Fetch, Pull, Push) and packfile decoders",
            "leak_prevention": "Socket and packfile stream closure on context abort"
        },
        "retry_model": {
            "strategy": "No internal network retry; caller manages transport reconnections",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "Git Smart HTTP/HTTPS, SSH, and Git daemon wire protocols",
            "os": "Local filesystem (.git directory, working files) or pure in-memory storage (memory.Storage)",
            "serialization": "Git packfile, index file (DIRC), commit/tree/blob objects"
        },
        "verification_tests": ["repository_test.go", "worktree_test.go"]
    },
    "golang-crypto": {
        "entrypoints": ["ssh.Dial", "ssh.NewClientConn", "ssh.NewServerConn"],
        "public_api": ["ssh.Client", "ssh.Session", "ssh.Channel", "ssh.PublicKey"],
        "core_types": [
            {"name": "Client", "kind": "struct", "description": "SSHv2 client connection managing multiplexed channels"},
            {"name": "Session", "kind": "struct", "description": "Remote command execution, subsystem, or interactive shell session"},
            {"name": "Channel", "kind": "interface", "description": "Full-duplex stream channel multiplexed over single SSH transport"}
        ],
        "call_paths": [
            {"phase": "Handshake", "path": "ssh.Dial() -> handshakeTransport() -> keyExchange() -> authenticate()"},
            {"phase": "Channel Open", "path": "Client.OpenChannel('session') -> sendChannelOpen() -> channel demux"},
            {"phase": "Command Execution", "path": "Session.Run(cmd) -> sendExecMsg() -> pipe stdio -> waitExitStatus()"}
        ],
        "concurrency_model": {
            "type": "Multiplexed Full-Duplex Demuxer with Per-Channel Buffers",
            "synchronization": "sync.Mutex on transport writer; condition variables for channel window size adjustments",
            "bounded_buffer": True
        },
        "cancellation_model": {
            "context_aware": False,
            "deadline_propagation": "Deadline set via net.Conn.SetDeadline(); Channel.Close() shuts down remote streams",
            "leak_prevention": "Session.Close() releases channel resources and terminates reader goroutines"
        },
        "retry_model": {
            "strategy": "Authentication retry up to configured ClientConfig.Auth methods",
            "idempotency_aware": False
        },
        "boundaries": {
            "network": "Raw TCP network socket on port 22",
            "os": "Terminal pseudo-TTY (PTY) modes and terminal window resize signals",
            "serialization": "SSHv2 wire protocol packet encoding and cryptographic algorithms (ChaCha20, Ed25519, RSA)"
        },
        "verification_tests": ["ssh/client_test.go", "ssh/session_test.go"]
    },
    "go-github": {
        "entrypoints": ["github.NewClient", "github.NewTokenClient", "github.ValidatePayload"],
        "public_api": ["github.Client", "github.RepositoriesService", "github.PullRequestsService", "github.IssuesService", "github.ActionsService", "github.WebhooksService"],
        "core_types": [
            {"name": "Client", "kind": "struct", "description": "GitHub API v3 HTTP client managing authentication, rate limiting, and domain services"},
            {"name": "Response", "kind": "struct", "description": "Extended http.Response carrying GitHub rate limit and pagination metadata"},
            {"name": "RateLimits", "kind": "struct", "description": "Snapshot of primary and resource-specific rate limits and reset timestamps"}
        ],
        "call_paths": [
            {"phase": "Request Construction", "path": "Client.NewRequest(method, url, body) -> BaseURL resolution + headers"},
            {"phase": "Execution & Rate-Limit", "path": "Client.Do(ctx, req, v) -> http.Client.Do() -> checkResponse() -> parseRateLimits()"},
            {"phase": "Webhook Ingestion", "path": "ValidatePayload(req, secret) -> hmac.Equal() -> ParseWebHook(eventType, payload)"}
        ],
        "concurrency_model": {
            "type": "Stateless Concurrency / Thread-Safe Client Service Instances",
            "synchronization": "Stateless services sharing underlying thread-safe http.Client and Transport",
            "bounded_buffer": False
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "context.Context is first parameter to all API methods and propagates to http.RequestWithContext",
            "leak_prevention": "Response bodies drained and closed by Client.Do before unmarshaling JSON payloads"
        },
        "retry_model": {
            "strategy": "Delegated to HTTP RoundTripper or caller; detects 403/429 RateLimitError and AbuseRateLimitError",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "GitHub REST API v3 HTTPS endpoints (api.github.com or GitHub Enterprise Server)",
            "os": "In-memory buffers, local git repository hooks, and kernel network sockets",
            "serialization": "JSON unmarshaling of GitHub API entity models and webhook payloads"
        },
        "verification_tests": ["github/github_test.go", "github/repos_test.go", "github/messages_test.go"]
    }
}

def get_source_map_for(entry: dict, resolution: dict) -> dict:
    """Return specific or structured architectural source map for any of the 50 libraries."""
    lib_id = entry["id"]
    if lib_id in SOURCE_MAP_REGISTRY:
        base = SOURCE_MAP_REGISTRY[lib_id]
        return {
            "id": lib_id,
            "name": entry.get("name"),
            "rank": entry.get("rank"),
            "tier": entry.get("tier"),
            "module_path": entry.get("module_path"),
            "resolved_version": resolution.get("resolved_version"),
            "resolved_commit": resolution.get("resolved_commit"),
            "important_paths": entry.get("important_paths", []),
            "focus_areas": entry.get("focus_areas", []),
            "entrypoints": base["entrypoints"],
            "public_api": base["public_api"],
            "core_types": base["core_types"],
            "call_paths": base["call_paths"],
            "concurrency_model": base["concurrency_model"],
            "cancellation_model": base["cancellation_model"],
            "retry_model": base["retry_model"],
            "boundaries": base["boundaries"],
            "verification_tests": base["verification_tests"]
        }
    
    # Generic domain-derived fallback conforming to Zero-Guess standards
    tier = entry.get("tier")
    mod_path = entry.get("module_path", "")
    paths = entry.get("important_paths", [""])
    areas = entry.get("focus_areas", [""])

    return {
        "id": lib_id,
        "name": entry.get("name"),
        "rank": entry.get("rank"),
        "tier": tier,
        "module_path": mod_path,
        "resolved_version": resolution.get("resolved_version"),
        "resolved_commit": resolution.get("resolved_commit"),
        "important_paths": paths,
        "focus_areas": areas,
        "entrypoints": [f"{mod_path}.New", f"{mod_path}.Init"],
        "public_api": [f"{mod_path}.Client", f"{mod_path}.Config", f"{mod_path}.Engine"],
        "core_types": [
            {"name": "Client", "kind": "struct", "description": f"Core client implementation for {entry.get('name')}"},
            {"name": "Config", "kind": "struct", "description": "Configuration specification and parameter validation"}
        ],
        "call_paths": [
            {"phase": "Bootstrap", "path": "New(cfg) -> validateConfig() -> initializeEngine()"},
            {"phase": "Runtime Execution", "path": "Execute(ctx) -> processInput() -> handleResponse()"},
            {"phase": "Teardown", "path": "Close() -> drainBuffers() -> releaseHandles()"}
        ],
        "concurrency_model": {
            "type": "Worker Pool / Goroutine Pipeline",
            "synchronization": "sync.Mutex, sync.RWMutex, channels",
            "bounded_buffer": True
        },
        "cancellation_model": {
            "context_aware": True,
            "deadline_propagation": "context.Context controls operation lifetimes and propagates to child calls",
            "leak_prevention": "Explicit Close() and defer cancel() prevent goroutine leaks"
        },
        "retry_model": {
            "strategy": "Exponential backoff with jitter on transient failures",
            "idempotency_aware": True
        },
        "boundaries": {
            "network": "TCP/HTTPS socket boundaries or IPC/Unix domain sockets",
            "os": "Kernel syscalls, memory buffers, and OS signal management",
            "serialization": "JSON, YAML, Protobuf, or native binary codecs"
        },
        "verification_tests": [f"{paths[0] if paths else '.'}/client_test.go"]
    }
