# RabbitMQ & Celery Support - Summary

## What's New

GenPulse now supports **three message queue backends**:

1. **Redis** (default) - Lightweight, fast, built-in
2. **RabbitMQ** - Enterprise-grade message broker
3. **Celery** - Distributed task queue with advanced features

## Quick Start

### Using Redis (Default)
```bash
# No configuration needed
uv run genpulse dev
```

### Using RabbitMQ
```bash
# 1. Start RabbitMQ
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management

# 2. Configure
export GENPULSE_MQ__TYPE=rabbitmq
export GENPULSE_MQ__RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# 3. Run
uv run genpulse dev
```

### Using Celery
```bash
# 1. Configure
export GENPULSE_MQ__TYPE=celery

# 2. Start Celery Worker
uv run celery -A genpulse.infra.mq.celery_app worker --loglevel=info -Q genpulse_tasks

# 3. Start API (in another terminal)
uv run uvicorn genpulse.app:create_api --reload
```

## Configuration

Add to your `.env` or `config/config.yaml`:

```yaml
mq:
  type: "redis"  # or "rabbitmq" or "celery"
  rabbitmq_url: "amqp://guest:guest@localhost:5672/"
  celery_broker_url: "redis://localhost:6379/0"
  celery_result_backend: "redis://localhost:6379/1"
```

## OpenAPI Generation

Generate OpenAPI specification:

```bash
python scripts/generate_openapi.py --output openapi.json
```

## Architecture Changes

- **TaskProcessor**: Extracted task processing logic for reusability
- **MQ Factory**: `get_mq()` now supports multiple backends
- **Hybrid State Storage**: RabbitMQ and Celery use Redis for task status caching

## Testing

```bash
# Test Celery MQ
uv run pytest tests/infra/test_celery_mq.py -v

# Test RabbitMQ (requires running RabbitMQ)
uv run pytest tests/infra/test_rabbitmq.py -v
```

## Next Steps

- [ ] Update main README.md
- [ ] Update AGENTS.md
- [ ] Add Dead Letter Queue (DLQ) support
- [ ] Implement rate limiting per provider
