# Docker Infrastructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Create a production-ready `docker-compose.yml` to spin up PostgreSQL, Redis, and MinIO for local development.

**Architecture:**
- **Postgres**: Version 16-alpine.
- **Redis**: Version 7-alpine.
- **MinIO**: Latest (S3 compatible storage).
- **Network**: Bridge network `genpulse-net`.

---

### Task 1: Docker Integration

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.docker` (Sample env)

**Step 1: Define Services**
- **postgres**: Expose 5432. Mount volume `pg_data`.
- **redis**: Expose 6379. Mount volume `redis_data`.
- **minio**: Expose 9000 (API) & 9001 (Console). Mount volume `minio_data`.
  - Command: `server /data --console-address ":9001"`

**Step 2: Define Volumes & Networks**
- Persistent volumes for all data.

---

### Task 2: Config Verification

**Files:**
- Modify: `README.md` / `README_CN.md`

**Step 1: Update Documentation**
- Add "Start Infrastructure" section using `docker-compose up -d`.
- Explain how to configure `.env` to point to MinIO if testing S3.

---

### Task 3: Infrastructure Verification

**Step 1: Test Connectivity**
- Use `test_smoke.py` or new `tests/test_infra.py` to check connecting to these containers.
- *Requires user to actually run `docker-compose up -d`*.

**Step 2: MinIO Setup Script (Optional)**
- Create a script `scripts/init_minio.py` to auto-create the 'genpulse' bucket.
