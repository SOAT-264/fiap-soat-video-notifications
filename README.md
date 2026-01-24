# 📧 Video Processor - Notification Service

Microserviço responsável pelo envio de notificações por email quando jobs são completados ou falham.

## 📐 Arquitetura

```
fiap-soat-video-notifications/
├── src/notification_service/
│   ├── domain/entities/          # Notification entity
│   ├── application/
│   │   ├── ports/                # INotificationRepository, IEmailSender
│   │   └── use_cases/            # SendNotification, HandleJobEvent
│   └── infrastructure/
│       ├── adapters/input/api/   # FastAPI routes
│       ├── adapters/output/
│       │   ├── persistence/      # PostgreSQL
│       │   ├── email/            # SMTP sender
│       │   └── cache/            # Redis
│       └── config/               # Settings
├── Dockerfile
└── pyproject.toml
```

## 🚀 Rodar Localmente

### Pré-requisitos

- Python 3.11+
- PostgreSQL rodando na porta 5434
- Servidor SMTP (ou Gmail com App Password)

### 1. Clone e instale

```bash
git clone https://github.com/morgadope/fiap-soat-video-notifications.git
cd fiap-soat-video-notifications
pip install -e ".[dev]"
```

### 2. Configure variáveis de ambiente

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5434/notification_db"
export REDIS_URL="redis://localhost:6379/3"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT=587
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM="noreply@video-processor.com"
```

### 3. Execute

```bash
uvicorn notification_service.infrastructure.adapters.input.api.main:app --reload --port 8004
```

### 4. Acesse

- Swagger: http://localhost:8004/docs
- Health: http://localhost:8004/health

## 📖 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/notifications` | Listar notificações do usuário |
| GET | `/health` | Health check |

### Exemplos

**Listar notificações:**
```bash
curl "http://localhost:8004/notifications?user_id=UUID" \
  -H "Authorization: Bearer $TOKEN"
```

## 📧 Templates de Email

### Job Completado
```
Assunto: ✅ Video Processing Complete: video.mp4

Olá!

Seu vídeo "video.mp4" foi processado com sucesso!

📊 Resultados:
- Frames extraídos: 120
- Status: COMPLETED

📥 Download: https://...

Atenciosamente,
Video Processor Team
```

### Job Falhou
```
Assunto: ❌ Video Processing Failed: video.mp4

Olá!

Infelizmente houve um erro ao processar seu vídeo "video.mp4".

❌ Erro: ...

Por favor, tente novamente.

Atenciosamente,
Video Processor Team
```

## 🐳 Docker

```bash
docker build -t notification-service .
docker run -p 8004:8004 \
  -e DATABASE_URL=... \
  -e SMTP_HOST=... \
  notification-service
```

## 🧪 Testes

```bash
pytest tests/ -v --cov=notification_service
```

## 📄 Licença

MIT License
