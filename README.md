# GenPulse

<div align="center">

**Enterprise-Grade AI Generation Orchestration Engine**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Celery](https://img.shields.io/badge/Celery-5.3%2B-green.svg)](https://docs.celeryq.dev/)

[English](README.md) | [中文](README_ZH.md)

</div>

---

**GenPulse** is a comprehensive backend infrastructure designed to bridge the gap between complex Generative AI capabilities and business applications. It provides a unified, coherent interface to orchestrate tasks across multiple cloud providers (SaaS) and local execution engines (PaaS/IaaS).

## ✨ Key Features

### 🔌 Multi-Provider Support
Unified abstraction layer for various top-tier AI providers. Switch providers instantly without changing your client code.
*   **Video Generation**: VolcEngine (PixelDance), Kling AI, MiniMax (Hailuo), Baidu (UniVid), Tencent (Hunyuan), DashScope (Wanx).
*   **Image Generation**: VolcEngine, DashScope (Wanx), Baidu (SDXL), Tencent, MiniMax.

### 🎨 Deep ComfyUI Integration
Treats ComfyUI as a robust execution backend engine.
*   **Template System**: Call complex workflows using simple JSON templates (`src/genpulse/templates`).
*   **ComfyEngine**: Dedicated engine handles WebSocket communication, queue management, and parameter injection.
*   **Performance**: Supports `SaveImageWebsocket` for zero-latency image retrieval (no disk I/O).

### ⚡ Unified Architecture
*   **Handlers & Engines**: Clear separation between Business Dispatchers (Handlers) and Execution Logic (Engines).
*   **RabbitMQ / Redis MQ**: High-concurrency task queue based on Celery.
*   **Unified Storage**: Auto-upload generated assets to S3/OSS/MinIO and return standardized URLs.

### 🛠 Developer Experience
*   **FastAPI**: Modern, async, typed Python framework.
*   **DevOps Ready**: One-click `docker-compose` deployment with PostgreSQL, Redis, and Flower.
*   **Admin Dashboard**: Built-in SQLAdmin for visual task management.

## 🚀 Quick Start

### 1. Using Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/isWangjianhua/GenPulse.git
cd GenPulse

# Configure Environment
cp .env.example .env
# Edit .env to set your API KEYS (VOLC_ACCESS_KEY, KLING_AK, etc.)

# Launch Stack
docker-compose up -d

# Access Services
# - API Docs:      http://localhost:8000/docs
# - Admin Panel:   http://localhost:8000/admin
# - Worker Monitor: http://localhost:5555
```

### 2. Local Development

```bash
# Install dependencies using uv
uv sync

# Run Development Server
# Starts API, Worker, and Flower automatically
uv run genpulse dev
```

## 📚 Documentation

Detailed documentation is available in [English](docs/en/) and [Chinese](docs/zh/).

*   [**Architecture Design**](docs/en/architecture_design.md): Understand the core concepts (Handlers, Engines, Clients).
*   [**API Reference**](docs/en/api.md): Detailed API endpoints and parameter specs.
*   [**Deployment Guide**](docs/en/deploy.md): How to deploy to production.


## 🧩 System Architecture

GenPulse adopts a Layered Architecture to decouple business logic from AI implementation details.

```mermaid
graph LR
    Client -->|HTTP/MQ| API[API Gateway]
    API -->|Push| Queue[(Message Queue)]
    Queue -->|Consume| Worker[Celery Worker]
    
    subgraph "Execution Layer"
        Worker -->|Dispatch| H[Handler]
        H -->|Execute| E_Comfy[Comfy Engine]
        H -->|Execute| E_Diff[Diffusers Engine]
        H -->|Call| C_Cloud[Cloud Clients]
    end
    
    subgraph "Providers"
        E_Comfy --> ComfyUI[ComfyUI Server]
        C_Cloud --> Volc[VolcEngine]
        C_Cloud --> Kling[Kling AI]
        C_Cloud --> Baidu[Baidu Cloud]
    end
```

## 🤝 Contributing

Contributions are welcome! Please check the [Contributing Guide](docs/en/dev/contributing.md) (Coming Soon).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
