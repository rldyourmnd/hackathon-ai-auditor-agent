# Backend_public Rebase Tasks - Critical Alignment

This document outlines critical tasks to align backend_public/ with the main backend/ architecture and make it a proper microservice.

## Critical Issues Identified

### 1. **Database Schema Mismatch** 🔴 PRIORITY 1
**Issue**: backend_public uses completely different database models than backend/
- backend_public: User authentication models (users, auth_accounts, sessions)
- backend/: Prompt analysis models (prompts, prompt_relations, analysis_results)

**Problems**:
- No shared data models or relationships
- Different primary key strategies (int vs UUID strings)
- backend_public missing core prompt analysis tables
- No integration with main Curestry prompt-base

**Required Actions**:
1. Migrate backend_public to use SQLModel instead of SQLAlchemy ORM
2. Add core prompt analysis tables from backend/models/prompts.py
3. Align UUID string primary keys across all tables
4. Create proper foreign key relationships to main backend

### 2. **Framework Inconsistency** 🔴 PRIORITY 1
**Issue**: Different architectural patterns and dependencies

**Current State**:
- backend/: SQLModel + AsyncSession + Pydantic v2 + Alembic
- backend_public/: SQLAlchemy ORM + Sync sessions + Poetry

**Problems**:
- No async session support
- Different configuration patterns
- Inconsistent error handling
- Missing integration with LangGraph pipeline

**Required Actions**:
1. Migrate to SQLModel for type-safe database operations
2. Implement async sessions with AsyncSession pattern
3. Align Pydantic Settings configuration with backend/core/config.py
4. Add proper error handling middleware

### 3. **Missing Core Integration** 🔴 PRIORITY 1
**Issue**: backend_public doesn't integrate with main Curestry analysis pipeline

**Missing Components**:
- No connection to analysis pipeline endpoints
- No integration with prompt-base management
- Missing LLM service integration
- No shared schemas or business logic

**Required Actions**:
1. Add proxy endpoints to main backend/ analysis pipeline
2. Implement shared schema models from backend/schemas/
3. Add authentication middleware for admin access
4. Create proper service layer integration

### 4. **Environment Configuration Gap** 🟡 PRIORITY 2
**Issue**: Different environment variable patterns

**Current Gaps**:
- No shared .env configuration
- Missing database connection alignment
- Different service discovery patterns
- Hardcoded internal service URLs

**Required Actions**:
1. Align environment variables with backend/core/config.py
2. Add proper service discovery configuration
3. Create unified Docker environment setup
4. Implement proper secrets management

### 5. **Docker Container Integration** 🟡 PRIORITY 2
**Issue**: backend_public runs in isolation, not integrated with main stack

**Problems**:
- Separate Docker setup from main infra/
- No shared network configuration
- Different port management
- Missing health check integration

**Required Actions**:
1. Integrate with main infra/docker-compose.yml
2. Add proper networking between services
3. Align health check patterns
4. Configure proper service dependencies

## Migration Priority Order

### Phase 1: Core Alignment (Week 1)
1. **Database Schema Migration**
   - Add backend_public tables to main backend/alembic/
   - Create shared migration for user management tables
   - Align primary key strategies (UUID strings)
   - Add foreign key relationships to core prompt tables

2. **Framework Alignment**
   - Migrate from SQLAlchemy ORM to SQLModel
   - Implement async session patterns
   - Align Pydantic Settings configuration
   - Add proper logging and error handling

### Phase 2: Service Integration (Week 1-2)
3. **API Integration**
   - Add proxy endpoints to main backend analysis pipeline
   - Implement shared authentication middleware
   - Create unified response schemas
   - Add proper CORS and security headers

4. **Business Logic Integration**
   - Share service layer components
   - Integrate with LLM services
   - Add prompt-base connectivity
   - Implement proper caching strategies

### Phase 3: Infrastructure Alignment (Week 2)
5. **Docker Integration**
   - Merge backend_public into main infra/ stack
   - Configure shared networking
   - Align environment variable management
   - Add proper health check integration

6. **Testing and Monitoring**
   - Add integration tests with main backend
   - Implement proper logging integration
   - Add monitoring and observability
   - Create deployment automation

## Breaking Changes Required

### 1. Database Model Changes
```python
# BEFORE (backend_public/app/models.py)
class User(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
# AFTER (aligned with backend/)
class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
```

### 2. Configuration Changes
```python
# BEFORE (backend_public/app/config.py)
database_url: str = Field(alias="DATABASE_URL")

# AFTER (aligned with backend/core/config.py)
database_url: str = Field(
    default="postgresql+asyncpg://curestry:secure_password@db:5432/curestry"
)
```

### 3. Session Management Changes
```python
# BEFORE (sync sessions)
def get_db() -> Generator:
    db = SessionLocal()

# AFTER (async sessions)
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
```

## Risk Mitigation

### 1. Data Migration Strategy
- Create backup of existing backend_public data
- Use Alembic migration scripts for schema changes
- Implement rollback procedures
- Test migration on development environment first

### 2. Service Continuity
- Maintain backward compatibility during transition
- Use feature flags for gradual rollout
- Implement proper health checks
- Create monitoring dashboards

### 3. Integration Testing
- Add comprehensive integration test suite
- Test all API endpoints with new schema
- Validate authentication flow end-to-end
- Performance test with realistic load

## Success Criteria

### Phase 1 Complete When:
- ✅ All database models use SQLModel with UUID primary keys
- ✅ Async session pattern implemented
- ✅ Configuration aligned with main backend
- ✅ All tests pass with new schema

### Phase 2 Complete When:
- ✅ Authentication flow works with frontend_public
- ✅ Proxy endpoints connect to main analysis pipeline
- ✅ All business logic properly integrated
- ✅ Performance meets requirements

### Phase 3 Complete When:
- ✅ Single Docker compose startup works
- ✅ All services communicate properly
- ✅ Monitoring and logging integrated
- ✅ Deployment automation functional

## Next Steps

1. **Start with rebase.md** - Review and approve this migration plan
2. **Create backendguidelines.md** - Detailed implementation guidelines
3. **Create backendtasks.md** - Specific task breakdown with assignments
4. **Begin Phase 1** - Database schema alignment and framework migration

---

**Created**: 2025-08-17  
**Status**: Ready for Implementation  
**Estimated Timeline**: 2-3 weeks for complete integration