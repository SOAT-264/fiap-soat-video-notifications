# Notification Service - fiap-soat-video-notifications

Microservice responsible for sending email notifications.

## Features

- **Email Notifications**: Send job completion and failure emails
- **Event Handling**: Listen to job events and trigger notifications
- **Notification History**: Track all sent notifications

## Architecture

```
src/notification_service/
├── domain/            # Domain entities and exceptions
├── application/       # Use cases and ports
│   ├── ports/        # Input/Output interfaces
│   └── use_cases/    # Business logic
└── infrastructure/   # Adapters and config
    ├── adapters/
    │   ├── input/    # API routes
    │   └── output/   # Email, Database, Cache
    └── config/       # Settings
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/notifications` | List user notifications |

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/3` |
| `SMTP_HOST` | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | - |
| `SMTP_PASSWORD` | SMTP password | - |
| `SMTP_FROM` | From address | `noreply@video-processor.com` |

## Running Locally

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the service
uvicorn notification_service.infrastructure.adapters.input.api.main:app --reload --port 8004

# Run with Docker
docker build -t notification-service .
docker run -p 8004:8004 notification-service
```

## Testing

```bash
pytest tests/ -v --cov=notification_service
```

## Dependencies

- **Internal**: `video-processor-shared` (shared library)
- **External**: PostgreSQL, Redis, SMTP Server
