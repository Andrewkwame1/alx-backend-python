# Kubernetes Scaling and Load Testing Script for PowerShell
Write-Host "=== Kubernetes Scaling and Load Testing Script ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$DEPLOYMENT_NAME = "django-messaging-app"
$NAMESPACE = "default"
$TARGET_REPLICAS = 3
$SERVICE_NAME = "django-messaging-service"
$PORT = 8000

# Function to check if a command exists
function Test-Command($cmdname) {
  return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check prerequisites
Write-Host "1. Checking prerequisites..." -ForegroundColor Yellow
if (-not (Test-Command "kubectl")) {
  Write-Host "ERROR: kubectl is not installed!" -ForegroundColor Red
  exit 1
}
Write-Host "✓ kubectl is installed" -ForegroundColor Green

if (-not (Test-Command "wrk")) {
  Write-Host "WARNING: wrk is not installed. Load testing will be skipped." -ForegroundColor Yellow
  Write-Host "Install wrk from: https://github.com/wg/wrk"
  $WRK_INSTALLED = $false
}
else {
  Write-Host "✓ wrk is installed" -ForegroundColor Green
  $WRK_INSTALLED = $true
}
Write-Host ""

# Scale the deployment
Write-Host "2. Scaling deployment to $TARGET_REPLICAS replicas..." -ForegroundColor Yellow
$scaleResult = kubectl scale deployment/$DEPLOYMENT_NAME --replicas=$TARGET_REPLICAS -n $NAMESPACE
if (-not $?) {
  Write-Host "ERROR: Failed to scale deployment" -ForegroundColor Red
  exit 1
}
Write-Host "✓ Deployment scaled successfully" -ForegroundColor Green
Write-Host ""

# Wait for pods to be ready
Write-Host "3. Waiting for pods to be ready..." -ForegroundColor Yellow
kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=120s
Write-Host ""

# Verify pods are running
Write-Host "4. Verifying pods are running..." -ForegroundColor Yellow
Write-Host "Current pod status:"
kubectl get pods -l app=django-messaging -n $NAMESPACE
$POD_COUNT = (kubectl get pods -l app=django-messaging -n $NAMESPACE --field-selector=status.phase=Running --no-headers | Measure-Object -Line).Lines
Write-Host ""
Write-Host "Running pods: $POD_COUNT/$TARGET_REPLICAS"
Write-Host ""

# Monitor resource usage (kubectl top)
Write-Host "5. Monitoring resource usage with kubectl top..." -ForegroundColor Yellow
Write-Host "Pod resource usage:"
$podTop = kubectl top pods -l app=django-messaging -n $NAMESPACE 2>$null
if ($?) {
  Write-Host $podTop
}
else {
  Write-Host "⚠ kubectl top failed - ensure metrics-server is installed" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Node resource usage:"
$nodeTop = kubectl top nodes 2>$null
if ($?) {
  Write-Host $nodeTop
}
else {
  Write-Host "⚠ kubectl top nodes failed - ensure metrics-server is installed" -ForegroundColor Yellow
}
Write-Host ""

# Load testing with wrk
if ($WRK_INSTALLED) {
  Write-Host "6. Setting up port forwarding for load testing..." -ForegroundColor Yellow
  $portForward = Start-Job -ScriptBlock { 
    param($SERVICE_NAME, $PORT, $NAMESPACE)
    kubectl port-forward service/$SERVICE_NAME $PORT`:$PORT -n $NAMESPACE
  } -ArgumentList $SERVICE_NAME, $PORT, $NAMESPACE
    
  Start-Sleep -Seconds 3
    
  Write-Host "7. Running load test with wrk..." -ForegroundColor Yellow
  try {
    wrk -t4 -c50 -d30s http://localhost:$PORT/
  }
  catch {
    Write-Host "⚠ Load test failed" -ForegroundColor Yellow
  }
    
  # Clean up port-forward
  Stop-Job -Job $portForward
  Remove-Job -Job $portForward
}
else {
  Write-Host "6. Skipping load test - wrk not installed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Final Status ===" -ForegroundColor Cyan
kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE
kubectl get pods -l app=django-messaging -n $NAMESPACE -o wide

Write-Host "Done." -ForegroundColor Green