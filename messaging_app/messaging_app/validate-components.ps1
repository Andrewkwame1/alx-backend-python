# Kubernetes Components Validation Script
Write-Host "=== Kubernetes Components Validation Script ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$NAMESPACE = "default"
$COMPONENTS = @(
  @{Name = "Main Deployment"; File = "deployment.yaml" },
  @{Name = "Blue Deployment"; File = "blue_deployment.yaml" },
  @{Name = "Green Deployment"; File = "green_deployment.yaml" },
  @{Name = "Service"; File = "kubeservice.yaml" },
  @{Name = "Ingress"; File = "ingress.yaml" }
)

# Function to validate YAML files
function Test-YamlFile {
  param (
    [string]$file,
    [string]$name
  )
  Write-Host "Validating $name ($file)..." -ForegroundColor Yellow
  try {
    $result = kubectl apply --dry-run=client -f $file 2>&1
    if ($?) {
      Write-Host "✓ $name validation successful" -ForegroundColor Green
      return $true
    }
    else {
      Write-Host "✗ $name validation failed: $result" -ForegroundColor Red
      return $false
    }
  }
  catch {
    Write-Host "✗ $name validation failed: $_" -ForegroundColor Red
    return $false
  }
}

# Function to check if Minikube is running
function Test-MinikubeStatus {
  try {
    $status = minikube status
    if ($?) {
      Write-Host "✓ Minikube is running" -ForegroundColor Green
      return $true
    }
    else {
      Write-Host "✗ Minikube is not running" -ForegroundColor Red
      return $false
    }
  }
  catch {
    Write-Host "✗ Minikube check failed: $_" -ForegroundColor Red
    return $false
  }
}

# Main validation process
Write-Host "1. Checking Minikube status" -ForegroundColor Yellow
if (-not (Test-MinikubeStatus)) {
  Write-Host "Please start Minikube before proceeding with validation" -ForegroundColor Red
  exit 1
}
Write-Host ""

Write-Host "2. Validating Kubernetes manifests" -ForegroundColor Yellow
$allValid = $true
foreach ($component in $COMPONENTS) {
  if (-not (Test-YamlFile -file $component.File -name $component.Name)) {
    $allValid = $false
  }
  Write-Host ""
}

Write-Host "3. Checking Ingress Controller" -ForegroundColor Yellow
$ingressPods = kubectl get pods -n ingress-nginx --no-headers 2>$null
if ($?) {
  Write-Host "✓ Ingress controller is installed" -ForegroundColor Green
}
else {
  Write-Host "✗ Ingress controller is not installed" -ForegroundColor Red
  Write-Host "Run: minikube addons enable ingress" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "4. Verifying Scripts" -ForegroundColor Yellow
$scripts = @("kurbeScript", "kubctl-0x01", "kubctl-0x02", "kubctl-0x03")
foreach ($script in $scripts) {
  if (Test-Path $script) {
    Write-Host "✓ $script exists" -ForegroundColor Green
  }
  else {
    Write-Host "✗ $script not found" -ForegroundColor Red
  }
}
Write-Host ""

Write-Host "5. Checking Docker Images" -ForegroundColor Yellow
$images = @(
  "andrewkwame1/django-messaging-app:1.0",
  "andrewkwame1/django-messaging-app:1.1",
  "andrewkwame1/django-messaging-app:2.0"
)
foreach ($image in $images) {
  $pullResult = docker pull $image 2>$null
  if ($?) {
    Write-Host "✓ Image $image is available" -ForegroundColor Green
  }
  else {
    Write-Host "✗ Image $image is not available" -ForegroundColor Red
  }
}

Write-Host ""
Write-Host "=== Validation Summary ===" -ForegroundColor Cyan
if ($allValid) {
  Write-Host "All components validated successfully!" -ForegroundColor Green
}
else {
  Write-Host "Some components failed validation. Please check the errors above." -ForegroundColor Red
}
Write-Host "Done." -ForegroundColor Green