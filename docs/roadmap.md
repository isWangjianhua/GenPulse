# Future Roadmap

This document outlines the strategic direction for GenPulse's development.

## Phase 1: Foundation (Completed)
- [x] Basic Async Architecture (FastAPI + Redis + Postgres)
- [x] Multi-Provider Support (VolcEngine, ComfyUI)
- [x] Robust Logging & Error Handling
- [x] Local Diffusers Engine (Mock Mode)

## Phase 2: User Experience (Next Up)
### 1. Web Dashboard (High Priority)
A visual interface to monitor the system in real-time.
- **Features**:
    - Live Task Queue visualization (Processing/Pending/Failed).
    - Asset Gallery: View generated images/videos.
    - System Health: Redis/DB latency metrics.
- **Tech Stack**: HTML5 / Vanilla JS (No build step required) + SSE (Server-Sent Events).

### 2. Video Capability Expansion
To become a true multi-modal engine, we need better video support.
- **Goal**: Unified `VideoHandler` capable of routing to:
    - **VolcEngine**: For high-quality commercial generation.
    - **ComfyUI**: For experimental workflows (AnimateDiff).
    - **Kling/Luma/Runway**: Future integration via API.
- **Feature**: Automatic "Image-to-Video" upscaling pipeline.

## Phase 3: Enterprise Features (Q2 2026)
- [ ] **Multi-Tenant Support**: API Key management per user.
- [ ] **Billing System**: Credit deduction per second of GPU usage.
- [ ] **Cluster Mode**: Horizontal scaling of Workers across multiple machines.
