# Messaging App - Django REST Framework API

## Overview

This project implements a complete messaging application using Django and Django REST Framework. It follows industry best practices for building robust RESTful APIs with proper data modeling, relationship management, and URL routing.

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