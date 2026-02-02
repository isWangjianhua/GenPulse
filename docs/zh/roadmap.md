# 未来路线图

本文档概述了 GenPulse 开发的战略方向。

## 阶段 1: 基础建设与连接性 (已完成)
- [x] 基础异步架构 (FastAPI + Redis + Postgres)
- [x] 健壮的日志与错误处理
- [x] 本地 Diffusers 引擎
- [x] **多供应商支持**: 集成 7+ 家云提供商。
- [x] **客户端抽象层**: `BaseClient`。
- [x] **MQ 抽象层**: `Celery` 集成。
- [x] **限流**: 分布式令牌桶限流。

## 阶段 2: 编排与健壮性 (已完成)
### 1. ComfyUI 深度集成
- [x] **ComfyEngine**: 负责 WebSocket 通信的专用引擎。
- [x] **模板系统**: 基于 JSON 的工作流模板 (`template_name`)。
- [x] **高性能**: `SaveImageWebsocket` 二进制捕获。

### 2. 统一 Handler
- [x] **通用调度器**: `ImageHandler` 和 `VideoHandler` 路由到正确的供应商或引擎。
- [x] **双模支持**: HTTP 轮询 + 直接 RPC。
- [x] **统一存储**: S3/OSS 自动上传。

## 阶段 3: 开发者体验 (当前重点)
### 1. Web Dashboard (看板)
让用户尝试生成能力的可视化界面。
- [ ] Next.js / React 前端。
- [ ] 实时进度条。
- [ ] 资产画廊。

### 2. SDK 生成
- [ ] **OpenAPI Spec**: 优化用于 SDK 生成的 Spec。
- [ ] **Client SDKs**: Python/TypeScript 客户端库。

## 阶段 4: 企业级特性 (2026 Q4)
- [ ] **多租户支持**: 每个用户的 API Key 管理。
- [ ] **计费系统**: 积分扣除模型。
- [ ] **集群模式**: 跨多台机器的 Worker 水平扩展。
