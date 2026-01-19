# Database Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Integrate PostgreSQL into GenPulse using SQLAlchemy (Async) and Alembic for migrations. Implement the initial `Task` model and persist task metadata.

**Architecture:**
- **PostgreSQL** as the primary relational database.
- **SQLAlchemy 2.0 (Async)** as the ORM.
- **Alembic** for schema migrations.

---

### Task 1: Database Setup & Configuration

**Files:**
- Modify: `core/config.py` (Already updated `DATABASE_URL`)
- Create: `core/db.py` (Database engine and session management)

**Step 1: Create core/db.py**
Implement async engine and sessionmaker.

**Step 2: Initialize Alembic**
Run `alembic init alembic` and configure it to use the `DATABASE_URL` from `core.config`.

---

### Task 2: Initial Models

**Files:**
- Create: `core/models.py`

**Step 1: Define Task Model**
Fields: `id`, `task_id` (uuid), `task_type`, `params` (JSONB), `status`, `progress`, `result` (JSONB), `created_at`, `updated_at`.

**Step 2: Register Models with Alembic**
Configure `alembic/env.py` to target the models for auto-migration.

---

### Task 3: Task Persistence in Gateway

**Files:**
- Modify: `core/gateway.py`

**Step 1: Update /task endpoint**
Instead of just returning a stub, insert a record into the `tasks` table with status `pending`.

---

### Task 4: Task Updates in Worker

**Files:**
- Modify: `core/worker.py`
- Modify: `core/mq.py` (Update status should sync to both Redis and DB)

**Step 1: Sync status updates**
Ensure `update_task_status` in `RedisManager` or a new `DBManager` updates the PostgreSQL record when the worker changes task state.

---

### Task 5: Verification

**Files:**
- Create: `tests/core/test_db.py`

**Step 1: Test CRUD**
Verify that creating a task via API persists it in the DB, and worker updates are reflected.
