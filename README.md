# fiap-soat-video-notifications

## Introdução
> Este repositório faz parte do projeto [FIAP SOAT Video Processor](https://github.com/SOAT-264/fiap-soat-video-local-dev).

Microserviço de notificações do ecossistema FIAP SOAT Video Processor. Ele disponibiliza API para consulta de notificações e worker para consumir eventos de job e enviar e-mails.

## Sumário
- Explicação do projeto
- Objetivo
- Como funciona
- Repositórios relacionados
- Integrações com outros repositórios
- Como executar
- Como testar

## Repositórios relacionados
- [fiap-soat-video-auth](https://github.com/SOAT-264/fiap-soat-video-auth)
- [fiap-soat-video-jobs](https://github.com/SOAT-264/fiap-soat-video-jobs)
- [fiap-soat-video-shared](https://github.com/SOAT-264/fiap-soat-video-shared)
- [fiap-soat-video-local-dev](https://github.com/SOAT-264/fiap-soat-video-local-dev)
- [fiap-soat-video-obs](https://github.com/SOAT-264/fiap-soat-video-obs)

## Explicação do projeto
O serviço possui duas frentes:
- API FastAPI para listagem de notificações por usuário.
- Worker SQS para consumo de eventos de processamento e envio de e-mail via SES.

As notificações são persistidas no banco para rastreabilidade e auditoria do fluxo.

## Objetivo
Garantir comunicação com o usuário ao longo do processamento de vídeos, principalmente em eventos de conclusão e falha.

## Como funciona
1. O worker consome mensagens da fila `notification-queue` (SQS), incluindo payloads encapsulados por SNS.
2. Para cada evento, ele identifica o tipo (`job_completed`, `job_failed`) e monta assunto/corpo da notificação.
3. Quando necessário, consulta o auth em `GET /auth/users/{user_id}` para obter e-mail do usuário.
4. Envia e-mail via SES e atualiza status da notificação no banco.
5. A API expõe `GET /notifications` para consulta histórica, além de `GET /health` e `GET /metrics`.

## Integrações com outros repositórios
| Repositório integrado | Como integra | Para que serve |
| --- | --- | --- |
| `fiap-soat-video-jobs` | Consome eventos de job (pipeline `job-events -> notification-queue`) | Disparar comunicação ao usuário após processamento |
| `fiap-soat-video-auth` | Chamada HTTP para `GET /auth/users/{user_id}` | Resolver e-mail do usuário de forma confiável |
| `fiap-soat-video-service` | Integração indireta via fluxo de jobs iniciado por upload | Fechar ciclo completo de notificação do processamento |
| `fiap-soat-video-shared` | Dependência compartilhada do ecossistema para contratos comuns | Manter consistência de tipos e contratos entre repositórios |
| `fiap-soat-video-local-dev` | Provisiona DB/Redis/LocalStack, deploy API+worker e filas SNS/SQS | Executar notificações no ambiente principal de desenvolvimento |
| `fiap-soat-video-obs` | Exposição de `/health` e `/metrics` para scraping | Monitorar disponibilidade e comportamento operacional |

## Como executar
### Pré-requisitos
- Python 3.11+
- Infra local recomendada via `fiap-soat-video-local-dev`

### Execução local da API
```powershell
cd /fiap-soat-video-notifications
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

$env:DATABASE_URL="postgresql+asyncpg://postgres:postgres123@localhost:5435/notification_db"
$env:REDIS_URL="redis://localhost:6379/3"
$env:AWS_ENDPOINT_URL="http://localhost:4566"
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="us-east-1"
$env:SQS_NOTIFICATION_QUEUE_URL="http://localhost:4566/000000000000/notification-queue"
$env:AUTH_SERVICE_URL="http://localhost:8001"
$env:SES_FROM_EMAIL="noreply@videoprocessor.local"

uvicorn notification_service.infrastructure.adapters.input.api.main:app --host 0.0.0.0 --port 8004 --reload
```

### Execução local do worker
```powershell
cd /fiap-soat-video-notifications
.\.venv\Scripts\Activate.ps1
python -m notification_service.infrastructure.adapters.input.sqs_consumer
```

### Execução integrada (recomendada)
```powershell
cd /fiap-soat-video-local-dev
.\start.ps1
```

## Como testar
```powershell
cd /fiap-soat-video-notifications
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

