# Messaging App - Django REST Framework API

## Overview

This project implements a complete messaging application using Django and Django REST Framework. It follows industry best practices for building robust RESTful APIs with proper data modeling, relationship management, and URL routing.

## Recent Updates - CI/CD Implementation

### 🔄 Continuous Integration & Deployment

#### Jenkins Pipeline Setup
- **Location:** `messaging_app/Jenkinsfile`
- **Features:**
  - Automated build pipeline with multiple stages
  - Python environment setup and dependency management
  - Automated testing with pytest
  - Coverage reporting with HTML reports
  - Docker image building and pushing
  - Cleanup procedures

```groovy
Stages:
1. Checkout (Source Code)
2. Setup Environment (Python + Dependencies)
3. Run Tests (pytest + Coverage)
4. Build Docker Image
5. Push to Docker Hub
6. Cleanup
```

#### GitHub Actions Workflows

1. **Testing Pipeline** (`/.github/workflows/ci.yml`)
   - Triggers: Push and Pull Requests
   - Features:
     - Python 3.11 environment setup
     - MySQL service container for tests
     - Dependency installation
     - Flake8 linting
     - pytest execution with coverage
     - Coverage report artifacts

2. **Docker Deployment** (`/.github/workflows/dep.yml`)
   - Triggers: Push to main branch
   - Features:
     - Docker Buildx setup
     - Secure credentials handling
     - Multi-platform build support
     - Automated pushing to Docker Hub
     - Version tagging (latest + commit SHA)

### 🐋 Docker Integration

#### Local Development
```bash
# Start Jenkins container
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts

# Build application image
docker build -t andrewkwame1/django-messaging-app:latest .
```

#### Container Registry
- Images hosted on Docker Hub
- Repository: `andrewkwame1/django-messaging-app`
- Tags:
  - `latest`: Most recent build
  - `{BUILD_NUMBER}`: Jenkins build versions
  - `{SHA}`: GitHub commit versions

### 🔐 Security & Credentials

#### Required Secrets
1. **GitHub Actions:**
   - `DOCKER_USERNAME`: Docker Hub username
   - `DOCKER_PASSWORD`: Docker Hub access token

2. **Jenkins:**
   - GitHub credentials
   - Docker Hub credentials

### 📊 Testing & Quality

#### Automated Tests
- Unit tests with pytest
- Coverage reporting
- HTML test reports
- JUnit XML output

#### Code Quality
- Flake8 linting
- Maximum line length: 120
- Ignored patterns: venv, migrations, __pycache__

### 🚀 Quick Start Guide

1. **Clone Repository**
   ```bash
   git clone https://github.com/Andrewkwame1/alx-backend-python.git
   cd alx-backend-python/messaging_app
   ```

2. **Setup Local Development**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

3. **Run Tests**
   ```bash
   pytest
   flake8 .
   ```

4. **Start Jenkins (Docker)**
   ```bash
   docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
     -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts
   ```

5. **Access Jenkins**
   - Open http://localhost:8080
   - Follow setup wizard
   - Install required plugins:
     - Git
     - Pipeline
     - ShiningPanda

## Features

- User management with custom authentication
- Conversation creation and management
- Real-time messaging within conversations
- RESTful API endpoints
- Proper database relationships (many-to-many, foreign keys)

## Project Structure

```
messaging_app/
├── messaging_app/          # Main project directory
│   ├── __init__.py
│   ├── settings.py         # Project settings
│   ├── urls.py            # Main URL routing
│   └── wsgi.py
├── chats/                  # Messaging app
│   ├── __init__.py
│   ├── admin.py           # Admin configuration
│   ├── apps.py
│   ├── models.py          # Data models
│   ├── serializers.py     # DRF serializers
│   ├── urls.py           # App-specific URLs
│   └── views.py          # API views
├── manage.py
└── README.md       # Dependencies
```

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd messaging_app
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Authentication
- User registration: `POST /api/auth/register/`
- User login: `POST /api/auth/login/`

### Conversations
- List conversations: `GET /api/conversations/`
- Create conversation: `POST /api/conversations/`
- Retrieve conversation: `GET /api/conversations/{id}/`
- Update conversation: `PUT /api/conversations/{id}/`
- Delete conversation: `DELETE /api/conversations/{id}/`
- Send message: `POST /api/conversations/{id}/send_message/`

### Messages
- List messages in conversation: `GET /api/conversations/{id}/messages/`

## Data Models

### User Model
- Extends Django's AbstractUser
- UUID primary key
- Custom fields: phone_number, role (guest, host, admin)
- Email-based authentication

### Conversation Model
- UUID primary key
- Many-to-many relationship with Users (participants)
- Timestamp for creation

### Message Model
- UUID primary key
- Foreign key to User (sender)
- Foreign key to Conversation
- Message content and timestamp

## Serializers

The project includes comprehensive serializers that handle:
- User data serialization
- Conversation data with nested participants
- Message data with sender information
- Proper validation for creating conversations and messages

## API Usage Examples

### Create a Conversation
```bash
curl -X POST http://localhost:8000/api/conversations/ \
  -H "Content-Type: application/json" \
  -d '{
    "participant_ids": ["user-uuid-1", "user-uuid-2"]
  }'
```

### Send a Message
```bash
curl -X POST http://localhost:8000/api/conversations/{conversation_id}/send_message/ \
  -H "Content-Type: application/json" \
  -d '{
    "message_body": "Hello, this is a test message"
  }'
```

### Get Conversation Messages
```bash
curl http://localhost:3000/api/conversations/{conversation_id}/messages/
```

## Testing

Run the Django test suite:
```bash
python manage.py test
```

Test API endpoints using tools like:
- Postman
- curl
- DRF's browsable API at `http://localhost:3000/api/`

## Best Practices Implemented

- ✅ Modular project structure with separate apps
- ✅ Proper model relationships (FK, M2M)
- ✅ RESTful URL routing
- ✅ Versioned API endpoints
- ✅ Environment configuration management
- ✅ Secure authentication system
- ✅ Comprehensive serialization
- ✅ Proper documentation

## Dependencies

- Django 3.2+
- Django REST Framework
- Python 3.8+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is created for educational purposes as part of the ALX Backend Python program.

## Kubernetes / Minikube quick-start (local validation)

This repository also includes Kubernetes manifests and helper scripts for local testing with Minikube. The manifests use sample Docker image names — update them to your registry or load images into Minikube before applying.

Sample image names used in manifests:
- `andrewkwame1/messaging-app:latest`
- `andrewkwame1/messaging-app:1.1`
- `andrewkwame1/messaging-app:2.0`

Quick steps (PowerShell on Windows):

```powershell
# 1) Start Docker Desktop
# 2) Start minikube with containerd (recommended)
minikube delete
minikube start --driver=docker --container-runtime=containerd --container-runtime-endpoint=unix:///var/run/containerd/containerd.sock --memory=4096 --cpus=2

# 3) Verify cluster
kubectl cluster-info
kubectl get pods -A

# 4) Load or publish images so Minikube can pull them
# Option A: push to Docker Hub and update manifests
# Option B: build locally and load into minikube:
minikube image load andrewkwame1/messaging-app:latest

# 5) Apply manifests
kubectl apply -f deployment.yaml
kubectl apply -f kubeservice.yaml
kubectl apply -f blue_deployment.yaml
kubectl apply -f green_deployment.yaml
kubectl apply -f ingress.yaml

# 6) Use helper scripts (PowerShell or bash) in this folder to scale and run tests
```

Notes:
- If you see errors involving `/var/run/cri-dockerd.sock`, start Minikube with `--container-runtime=containerd` (see step 2).
- To enable ingress (NGINX) run: `minikube addons enable ingress`.
- Replace the sample image names with your real registry path or use `minikube image load` for local images.