# MH-CyberScore Backend Skill

## Description
Guide for building the MH-CyberScore FastAPI backend with SQLAlchemy, Pydantic, Alembic, and Celery. Use when creating API endpoints, database models, schemas, services, or any Python backend code for this project.

## Stack
- **Python 3.12+** with type hints everywhere
- **FastAPI 0.115+** — API framework
- **SQLAlchemy 2.0+** — ORM (async with asyncpg)
- **Alembic 1.14+** — DB migrations
- **PostgreSQL 16 + TimescaleDB** — main database
- **Pydantic 2.10+** — schemas/validation
- **Celery 5.4+ with Redis** — async task queue
- **Redis 7** — cache, sessions, rate limiting
- **httpx 0.28+** — async HTTP client

## Code Conventions

### Python Style
- Formatter: `ruff format` (line-length = 100)
- Linter: `ruff check` (rules: ALL except D203, D213)
- Type checker: `mypy --strict`
- Docstrings: Google style
- Tests: pytest with coverage > 80%
- Async: use async/await for ALL I/O (httpx, DB queries)
- Error handling: custom exceptions inheriting from `MHCyberScoreError`

### Naming
- Classes: PascalCase (VendorScoring, OsintAgent)
- Functions/methods: snake_case (calculate_score, fetch_dns_records)
- Constants: UPPER_SNAKE_CASE (MAX_RETRY_COUNT, SCORING_WEIGHTS)
- Modules: snake_case (scoring_engine.py, osint_agent.py)

### Project Structure
```
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/versions/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app factory
│   ├── config.py        # Settings (pydantic-settings)
│   ├── database.py      # SQLAlchemy engine + session
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic schemas (API contracts)
│   ├── api/v1/          # Route handlers
│   ├── api/deps.py      # Dependencies (auth, db session)
│   ├── services/        # Business logic
│   ├── agents/          # Celery AI workers
│   ├── tools/           # MCP tools for agents
│   ├── templates/       # Report & email templates
│   └── utils/           # Utilities
├── tests/
└── Dockerfile
```

### FastAPI Patterns

#### App Factory (main.py)
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import router as api_v1_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title="MH-CyberScore API",
        version="1.0.0",
        docs_url="/api/docs" if settings.debug else None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_v1_router, prefix="/api/v1")
    return app

app = create_app()
```

#### Config (config.py)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MH_")

    debug: bool = False
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    keycloak_url: str
    keycloak_realm: str = "mh-cyberscore"
    cors_origins: list[str] = ["http://localhost:3000"]
    jwt_secret_key: str
    jwt_algorithm: str = "RS256"

settings = Settings()
```

#### Database (database.py)
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

#### Model Pattern
```python
from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    tier: Mapped[int] = mapped_column(default=3)  # 1=critical, 2=important, 3=standard
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    scores: Mapped[list["VendorScore"]] = relationship(back_populates="vendor")
```

#### Schema Pattern
```python
from pydantic import BaseModel, Field
from datetime import datetime

class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=3, max_length=255)
    tier: int = Field(default=3, ge=1, le=3)

class VendorCreate(VendorBase):
    pass

class VendorResponse(VendorBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
```

#### API Route Pattern
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.vendor import VendorCreate, VendorResponse
from app.services.vendor_service import VendorService

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    service = VendorService(db)
    return await service.create(vendor)
```

### Sovereignty Rules (NON-NEGOTIABLE)
- NO AWS, GCP, Azure for scoring data → OVHcloud SecNumCloud or Scaleway
- NO direct OpenAI/Anthropic US APIs → self-hosted LLM via vLLM
- NO US CDN (Cloudflare) → European alternatives
- E2E encryption with MH-managed keys (HSM)
- All logs on French soil exclusively
- NEVER hardcode secrets → use environment variables

### Dependencies (pyproject.toml)
```toml
[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115"
uvicorn = {version = "^0.34", extras = ["standard"]}
sqlalchemy = "^2.0"
alembic = "^1.14"
psycopg = {version = "^3.2", extras = ["binary"]}
celery = {version = "^5.4", extras = ["redis"]}
redis = "^5.2"
pydantic = "^2.10"
pydantic-settings = "^2.7"
httpx = "^0.28"
python-jose = {version = "^3.3", extras = ["cryptography"]}
passlib = {version = "^1.7", extras = ["bcrypt"]}
python-multipart = "^0.0.18"
jinja2 = "^3.1"
weasyprint = "^63"
python-pptx = "^1.0"
openpyxl = "^3.1"
qdrant-client = "^1.12"
langchain = "^0.3"
dnspython = "^2.7"
cryptography = "^44"
```
