# ADR-002: Vertical Slice Architecture

**Date:** 2025-02-21
**Status:** Accepted
**Decider:** Preetam
**Modules Affected:** All (this is the foundational architecture decision)

---

## Context

ScholarPath starts with one exam but is designed to grow to multiple boards,
exam types, and thousands of students. The team plans to use AI coding tools
(Claude Code) heavily. A flat MVC structure would hit two walls quickly:
(1) once the codebase exceeds the AI context window, suggestions become
unreliable; (2) as features multiply, circular dependencies make changes
risky. The article that inspired this project explicitly describes this
problem and its solution: small, focused vertical slices with clear contracts.

---

## Decision

We will structure both backend and frontend as vertical slices. Each module
(auth, user, catalog, question, attempt, analysis, media, admin) owns its
routes, models, schemas, service, repository, and tests. Modules communicate
only through their public service interfaces — never through direct internal
imports. The admin module is a pure orchestrator with zero business logic.

---

## Alternatives Considered

### Option 1: Standard MVC (models/, views/, controllers/)
Traditional layered architecture.
- Pro: Familiar, easy to scaffold
- Con: Cross-cutting concerns create horizontal dependencies fast
- Con: Once codebase grows, AI context window fills with unrelated code
- Con: A change in "models" can break anything in "views" silently

### Option 2: Microservices from day one
Each module is a separate deployed service.
- Pro: True isolation, independent scaling
- Con: Massive operational complexity for a startup
- Con: Network calls between services for every exam fetch
- Con: Premature optimization — we don't know our bottlenecks yet

### Option 3: Vertical Slices (Modular Monolith) ← CHOSEN
Each feature area is a self-contained module within one deployable unit.
- Pro: AI context window = one module at a time (manageable)
- Pro: Each module has a clear contract — easy to explain to Claude Code
- Pro: Easy extraction to microservice later if one module needs independent scaling
- Con: Requires discipline to not break boundaries
- Con: Slightly more initial scaffolding than flat MVC

---

## Consequences

### Positive
- Claude Code sessions stay focused: "today we work on attempt module only"
- Module contracts serve as natural documentation for AI prompting
- New developers (or AI) can understand one module without reading everything
- Admin module growing too large is architecturally impossible by design

### Negative
- More initial folder structure to create
- Developers must resist the temptation to import across module internals
- Shared utilities (/shared) must be carefully governed to avoid becoming a junk drawer

### Neutral
- Testing is per-module: unit tests for services, integration tests for routers
- Deployment is still one unit (monolith) — no extra infra complexity

---

## Module Impact

```
Backend structure:
/backend/app/modules/auth/      → router, models, schemas, service, dependencies, tests
/backend/app/modules/user/      → router, models, schemas, service, repository, tests
/backend/app/modules/catalog/   → router, models, schemas, service, repository, tests
/backend/app/modules/question/  → router, models, schemas, service, repository, importer, tests
/backend/app/modules/attempt/   → router, models, schemas, service, state_machine, tests
/backend/app/modules/analysis/  → router, schemas, service, scorer, recommender, tests
/backend/app/modules/media/     → router, schemas, service, providers/, tests
/backend/app/modules/admin/     → router, schemas (no models, no service logic)
/backend/app/shared/            → pagination, exceptions, i18n, logging (NO business logic)

Frontend structure:
/frontend/src/modules/auth/     → api, components, pages, store, index.js
/frontend/src/modules/exam/     → api, components, pages, index.js
/frontend/src/modules/attempt/  → api, components, pages, hooks, store, index.js
/frontend/src/modules/analysis/ → api, components, pages, index.js
/frontend/src/modules/dashboard/→ components, pages, index.js
/frontend/src/modules/parent/   → api, components, pages, index.js
/frontend/src/modules/admin/    → api, components, pages, index.js
/frontend/src/shared/           → components, layouts, hooks, i18n
```

---

## Implementation Notes

Cross-module import rule (enforced by code review):
```python
# CORRECT — using public interface
from app.modules.auth.dependencies import verify_token
from app.modules.catalog.service import CatalogService

# WRONG — importing module internals
from app.modules.auth.models import User         # Never
from app.modules.catalog.repository import _raw  # Never
```

Frontend module export rule:
```javascript
// Each module's index.js exports ONLY public API
// CORRECT
import { LoginPage, useAuthStore } from '@/modules/auth'

// WRONG
import LoginForm from '@/modules/auth/components/LoginForm'
```

The admin module never contains:
- SQLAlchemy models
- Business logic functions
- Direct database queries

---

## Review Trigger

Revisit when a single module exceeds 2000 lines of code — that's a signal
it needs to be split into sub-modules. Revisit when traffic analysis shows
one module (e.g. analysis) needs independent scaling — that's when to
extract it to a microservice.
