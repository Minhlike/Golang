$ErrorActionPreference = 'Stop'
$missing = @()
foreach ($command in 'docker', 'kubectl', 'kind') {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        $missing += $command
    }
}
if ($missing.Count -gt 0) {
    throw "Missing local prerequisite(s): $($missing -join ', '). Install them before this real-tool lab; do not substitute a cloud cluster."
}
docker version --format '{{.Server.Version}}'
kubectl version --client=true
kind version
