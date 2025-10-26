<#
.SYNOPSIS
  Start Minikube (Windows) and verify cluster info and pods.

USAGE
  Open PowerShell and run:
  .\kurbeScript.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "Checking for minikube..."
if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    Write-Error "minikube not found. Install minikube: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
}

Write-Host "Starting minikube..."
minikube start --driver=docker

Write-Host "Verifying cluster..."
kubectl cluster-info

Write-Host "Retrieving pods (all namespaces)..."
kubectl get pods --all-namespaces

Write-Host "Done."