<#
.SYNOPSIS
  Start Minikube (Windows) and verify cluster info and pods.

USAGE
  Open PowerShell (Run as Administrator if starting Minikube with Hyper-V) and run:
    .\messaging_app\kurbeScript.ps1

  Or to bypass execution policy:
    powershell -ExecutionPolicy Bypass -File .\messaging_app\kurbeScript.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "Checking for minikube..."
if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    Write-Error "minikube not found. Install minikube: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
}

Write-Host "Checking for kubectl..."
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Error "kubectl not found. Install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
}

Write-Host "Checking for docker (to use the docker driver)..."
$dockerExists = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerExists) {
    try {
        docker info | Out-Null
        Write-Host "Docker is available."
    } catch {
        Write-Warning "Docker command exists but Docker daemon may not be running. Make sure Docker Desktop is started."
    }
} else {
    Write-Warning "Docker CLI not found. If you plan to use the Docker driver, install Docker Desktop and start it."
}

# Preferred: docker driver. If you need Hyper-V, run this script as Admin and pass driver hyperv when starting manually.
Write-Host "Starting minikube using the docker driver (recommended when Docker Desktop is running)..."
try {
    minikube start --driver=docker
} catch {
    Write-Warning "minikube start failed: $($_.Exception.Message)"
    Write-Host "Common fixes:"
    Write-Host " - Ensure Docker Desktop is installed and running."
    Write-Host " - If you previously used a different driver, run: minikube delete";
    Write-Host " - Try to explicitly set the driver: minikube config set driver docker; minikube start --driver=docker"
    Write-Host " - For Hyper-V users: run PowerShell as Admin, create a virtual switch and start with --driver=hyperv --hyperv-virtual-switch '<switch-name>'"
    exit 1
}

Write-Host "Verifying cluster..."
kubectl cluster-info

Write-Host "Retrieving pods (all namespaces)..."
kubectl get pods --all-namespaces

Write-Host "Done."
