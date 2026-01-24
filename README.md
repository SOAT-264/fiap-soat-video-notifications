# 📧 Video Processor - Notification Service

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Microserviço responsável pelo envio de notificações por email quando jobs são completados ou falham.

## 📋 Índice

- [Arquitetura](#-arquitetura)
- [Templates de Email](#-templates-de-email)
- [API Endpoints](#-api-endpoints)
- [Como Executar](#-como-executar)
- [AWS Lambda](#-aws-lambda)
- [Testes](#-testes)

---

## 🏗️ Arquitetura

```
src/notification_service/
├── domain/
│   └── entities/notification.py  # Entidade Notification
├── application/
│   ├── ports/output/             # IEmailSender
│   └── use_cases/                # SendNotification
└── infrastructure/
    ├── adapters/
    │   ├── input/
    │   │   ├── api/              # FastAPI routes
    │   │   └── sqs_consumer.py   # Lambda handler
    │   └── output/
    │       ├── persistence/      # SQLAlchemy
    │       └── email/            # SES sender
    └── config/
```

---

## 📧 Templates de Email

### Job Completado ✅

```
Assunto: ✅ Video Processing Complete: video.mp4

Olá!

Seu vídeo "video.mp4" foi processado com sucesso!

📊 Resultados:
- Frames extraídos: 120
- Status: COMPLETED

📥 Download: [link]

Atenciosamente,
Video Processor Team
```

### Job Falhou ❌

```
Assunto: ❌ Video Processing Failed: video.mp4

Olá!

Infelizmente houve um erro ao processar seu vídeo "video.mp4".

❌ Erro: [mensagem de erro]

Por favor, tente novamente.

Atenciosamente,
Video Processor Team
```

---

## 📡 API Endpoints

| Método | Endpoint | Descrição | Autenticação |
|--------|----------|-----------|--------------|
| GET | `/notifications` | Listar notificações | ✅ JWT |
| GET | `/health` | Health check | ❌ |

---

## 🚀 Como Executar

### Pré-requisitos

- Python 3.11+
- PostgreSQL
- AWS SES (ou LocalStack)

### 1. Clone e instale

```bash
git clone https://github.com/morgadope/fiap-soat-video-notifications.git
cd fiap-soat-video-notifications
pip install -e ".[dev]"
```

### 2. Configure

```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5435/notification_db"
export AWS_ENDPOINT_URL="http://localhost:4566"
export SES_FROM_EMAIL="noreply@videoprocessor.local"
export SQS_NOTIFICATION_QUEUE_URL="http://localhost:4566/000000000000/notification-queue"
```

### 3. Execute API

```bash
uvicorn notification_service.infrastructure.adapters.input.api.main:app --reload --port 8004
```

### 4. Execute Consumer (outro terminal)

```bash
python -m notification_service.infrastructure.adapters.input.sqs_consumer
```

---

## ☁️ AWS Lambda

O serviço pode rodar como Lambda triggered por SQS (subscribed to SNS):

```python
# sqs_consumer.py
def lambda_handler(event, context):
    for record in event["Records"]:
        body = json.loads(record["body"])
        await send_notification(body)
```

### Fluxo SNS → SQS → Lambda

```
Job Service → SNS (job-events) → SQS (notification-queue) → Lambda → SES
```

---

## 🐳 Docker

```bash
docker build -t notification-service .
docker run -p 8004:8004 \
  -e DATABASE_URL="..." \
  -e AWS_ENDPOINT_URL="..." \
  notification-service
```

---

## ⚙️ Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL PostgreSQL | - |
| `AWS_ENDPOINT_URL` | Endpoint AWS/LocalStack | - |
| `SES_FROM_EMAIL` | Email remetente | noreply@videoprocessor.local |
| `SQS_NOTIFICATION_QUEUE_URL` | URL da fila | - |

---

## 🧪 Testes

```bash
pytest tests/ -v --cov=notification_service
```

---

## 📄 Licença

MIT License
