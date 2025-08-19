"""
🗄️ Convergio - Database Management
Async SQLAlchemy 2.0 + PostgreSQL with connection pooling
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import structlog
from sqlalchemy import event, pool, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from core.config import get_settings

logger = structlog.get_logger()

# Test-environment compatibility: provide helper for mocking get_async_session
try:
    import sys
    from unittest.mock import AsyncMock
    from contextlib import asynccontextmanager
    
    if "pytest" in sys.modules:
        @asynccontextmanager
        async def create_mock_async_session_with_behavior(mock_session):
            """Helper to create a mock context manager that simulates get_async_session behavior.
            
            This is used by tests when they need to mock get_async_session but still want
            the transaction handling behavior (commit/rollback/close).
            """
            try:
                yield mock_session
                # Try to commit if no exception occurred
                if hasattr(mock_session, 'commit'):
                    await mock_session.commit()
            except Exception:
                # Rollback on any exception
                if hasattr(mock_session, 'rollback'):
                    await mock_session.rollback()
                raise
            finally:
                # Always close the session
                if hasattr(mock_session, 'close'):
                    await mock_session.close()
        
        # Export for tests to use
        _test_mock_session_helper = create_mock_async_session_with_behavior
except Exception:
    pass

# Global database components
# 'engine' is provided for test patching convenience
engine: Optional[AsyncEngine] = None
async_engine: Optional[AsyncEngine] = None
async_read_engine: Optional[AsyncEngine] = None  # Read replica engine
async_session_factory: Optional[async_sessionmaker] = None
async_read_session_factory: Optional[async_sessionmaker] = None  # Read replica sessions


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class CustomAsyncSession(AsyncSession):
    """AsyncSession that accepts plain SQL strings by auto-wrapping with text().

    This maintains backward compatibility with tests or legacy code that call
    session.execute("SELECT 1") without sqlalchemy.text().
    """

    async def execute(self, statement, params=None, execution_options=None):
        if isinstance(statement, str):
            statement = text(statement)
        return await super().execute(statement, params=params, execution_options=execution_options)


def create_database_engine(is_read_replica: bool = False) -> AsyncEngine:
    """Create async database engine with optimized settings
    
    Args:
        is_read_replica: Whether this is for a read replica connection
    """
    
    settings = get_settings()
    
    # Use read replica URL if available and requested
    # Prefer SQLite for tests unless explicitly disabled
    db_url = settings.DATABASE_URL
    if settings.ENVIRONMENT == "test" and os.getenv("USE_SQLITE_FOR_TESTS", "true").lower() in ("1", "true", "yes"):
        db_url = os.getenv("TEST_DB_URL", "sqlite+aiosqlite:///./test.db")
    if is_read_replica and hasattr(settings, 'DATABASE_READ_URL'):
        db_url = settings.DATABASE_READ_URL
    
    # Special-case SQLite for test environments to avoid requiring Postgres
    is_sqlite = str(db_url).startswith("sqlite:") or str(db_url).startswith("sqlite+")
    if is_sqlite:
        engine = create_async_engine(
            db_url,
            echo=settings.ENVIRONMENT in ("development", "test"),
            future=True,
        )
    else:
        engine = create_async_engine(
            db_url,
            # Connection pool settings
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Validate connections before use
            poolclass=AsyncAdaptedQueuePool,
            
            # Performance settings
            echo=settings.ENVIRONMENT == "development",  # SQL logging in dev
            echo_pool=settings.DEBUG,  # Pool logging for debugging
            future=True,  # Use SQLAlchemy 2.0 style
            
            # Async settings (Postgres/asyncpg specific)
            connect_args={
                "command_timeout": 30,
                "server_settings": {
                    "jit": "off",  # Disable JIT for better performance
                    "application_name": "convergio_backend",
                },
            },
        )
    
    try:
        safe_url = settings.DATABASE_URL
        if "@" in safe_url:
            safe_url = safe_url.split("@", 1)[1]
    except Exception:
        safe_url = "(hidden)"
    logger.info(
        "📊 Database engine created",
        url=safe_url,
        pool_size=getattr(settings, "DB_POOL_SIZE", None),
        max_overflow=getattr(settings, "DB_POOL_OVERFLOW", None),
    )
    
    return engine

async def init_db() -> None:
    """Initialize database connection and session factory"""
    
    global engine, async_engine, async_read_engine, async_session_factory, async_read_session_factory
    
    try:
        # Use pre-configured engine if provided (tests may patch 'engine')
        if engine is None:
            engine = create_database_engine(is_read_replica=False)
        async_engine = engine
        
        # Create session factory for primary
        async_session_factory = async_sessionmaker(
            async_engine,
            class_=CustomAsyncSession,
            expire_on_commit=False,  # Keep objects usable after commit
            autoflush=True,  # Auto-flush before queries
            autocommit=False,  # Explicit transaction control
        )
        
        # Create read replica engine and session factory if configured
        settings = get_settings()
        if hasattr(settings, 'DATABASE_READ_URL') and settings.DATABASE_READ_URL:
            async_read_engine = create_database_engine(is_read_replica=True)
            async_read_session_factory = async_sessionmaker(
                async_read_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,  # Read-only, no flush needed
                autocommit=False,
            )
            logger.info("✅ Read replica database configured")
        else:
            # Fallback to primary for reads if no replica
            async_read_engine = async_engine
            async_read_session_factory = async_session_factory
            logger.info("ℹ️ No read replica configured, using primary for reads")
        
        # Test connection and (optionally) ensure basic schema in test/dev
        # Use the test-patched engine for initialization if present
        base_engine = engine or async_engine
        begin_ctx = base_engine.begin()
        if asyncio.iscoroutine(begin_ctx) or hasattr(begin_ctx, "__await__"):
            begin_ctx = await begin_ctx
        async with begin_ctx as conn:
            # Ensure required extension (Postgres only)
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("🧩 Ensured pgvector extension present")
            except Exception as ext_e:
                logger.warning("⚠️ Unable to ensure pgvector extension", error=str(ext_e))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))

            # Optionally auto-create tables (disabled by default to avoid partial metadata issues)
            # Enable via AUTO_CREATE_DB_TABLES=true when needed (e.g., local dev with SQLite)
            if os.getenv("AUTO_CREATE_DB_TABLES", "false").lower() in ("1", "true", "yes"):
                try:
                    from core.database import Base as _Base
                    await conn.run_sync(_Base.metadata.create_all)
                    logger.info("🧱 Database tables ensured (env-flag enabled)")
                except Exception as ce:
                    logger.warning("⚠️ Table auto-create skipped/failed", error=str(ce))
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error("❌ Failed to initialize database", error=str(e))
        raise


async def ensure_dev_schema() -> None:
    """Lightweight dev-only auto-migration for known schema drift issues.

    - Adds document_embeddings.document_id column if missing
    - Adds FK constraint to documents(id) if missing
    """
    settings = get_settings()
    if settings.ENVIRONMENT != "development":
        return
    global async_engine
    if not async_engine:
        return
    try:
        async with async_engine.begin() as conn:
            # Check existing columns
            res = await conn.execute(text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'document_embeddings'
                """
            ))
            cols = {row[0] for row in res.fetchall()}
            # Columns to ensure exist (add as nullable to avoid issues on existing rows)
            ensure_columns = {
                "document_id": "INTEGER",
                "chunk_index": "INTEGER",
                "chunk_text": "TEXT",
                "embedding": "JSON",
                "embed_metadata": "JSON",
                "created_at": "TIMESTAMPTZ DEFAULT NOW()",
            }
            for col_name, col_type in ensure_columns.items():
                if col_name not in cols:
                    await conn.execute(text(
                        f"ALTER TABLE public.document_embeddings ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                    ))
                    logger.info("🛠️ Added missing column", table="document_embeddings", column=col_name)

            # Ensure id column is identity (auto-increment)
            try:
                res_ident = await conn.execute(text(
                    """
                    SELECT is_identity, column_default FROM information_schema.columns
                    WHERE table_schema='public' AND table_name='document_embeddings' AND column_name='id'
                    """
                ))
                row_ident = res_ident.fetchone()
                is_identity_val = row_ident[0] if row_ident else None
                has_default = row_ident and row_ident[1]
                if is_identity_val is None or str(is_identity_val).upper() != 'YES':
                    # Try to set identity first
                    try:
                        await conn.execute(text(
                            "ALTER TABLE public.document_embeddings ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY"
                        ))
                        logger.info("🔑 Enabled identity on document_embeddings.id")
                    except Exception:
                        # Fallback to sequence/default
                        await conn.execute(text(
                            "CREATE SEQUENCE IF NOT EXISTS public.document_embeddings_id_seq OWNED BY public.document_embeddings.id"
                        ))
                        await conn.execute(text(
                            "ALTER TABLE public.document_embeddings ALTER COLUMN id SET DEFAULT nextval('public.document_embeddings_id_seq')"
                        ))
                        logger.info("🔑 Ensured default sequence on document_embeddings.id")
                    # Ensure NOT NULL and PK
                    await conn.execute(text(
                        "ALTER TABLE public.document_embeddings ALTER COLUMN id SET NOT NULL"
                    ))
                    await conn.execute(text(
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.table_constraints
                                WHERE table_schema='public' AND table_name='document_embeddings'
                                  AND constraint_type='PRIMARY KEY'
                            ) THEN
                                ALTER TABLE public.document_embeddings ADD CONSTRAINT document_embeddings_pkey PRIMARY KEY (id);
                            END IF;
                        END $$;
                        """
                    ))
            except Exception as ident_e:
                logger.warning("⚠️ Unable to set identity on id column", error=str(ident_e))

            # Ensure created_at default now()
            try:
                await conn.execute(text(
                    "ALTER TABLE public.document_embeddings ALTER COLUMN created_at SET DEFAULT NOW()"
                ))
                logger.info("⏱️ Set default NOW() on document_embeddings.created_at")
            except Exception as ts_e:
                logger.warning("⚠️ Unable to set default on created_at", error=str(ts_e))

            # Ensure embedding column is of type vector (convert if needed)
            try:
                res_types = await conn.execute(text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema='public' AND table_name='document_embeddings' AND column_name='embedding'
                    """
                ))
                row = res_types.fetchone()
                if row and row[0] != 'vector':
                    # Try to alter column type to vector; cast from JSON/text via pgvector
                    # Note: assumes JSON array of floats stored as text; we recreate from text -> vector
                    await conn.execute(text(
                        "ALTER TABLE public.document_embeddings ALTER COLUMN embedding TYPE vector USING (to_vector(embedding::text))"
                    ))
                    logger.info("🔄 Converted embedding column to vector type")
            except Exception as conv_e:
                logger.warning("⚠️ Unable to convert embedding column to vector type", error=str(conv_e))

            # Ensure FK constraint exists
            await conn.execute(text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE table_schema='public' AND table_name='document_embeddings'
                          AND constraint_type='FOREIGN KEY'
                          AND constraint_name='document_embeddings_document_id_fkey'
                    ) THEN
                        ALTER TABLE public.document_embeddings
                        ADD CONSTRAINT document_embeddings_document_id_fkey
                        FOREIGN KEY (document_id)
                        REFERENCES public.documents(id)
                        ON DELETE CASCADE;
                    END IF;
                END $$;
                """
            ))
            logger.info("🔗 Ensured FK for document_embeddings.document_id -> documents.id")
    except Exception as e:
        # Non-fatal in dev, but log
        logger.warning("⚠️ Dev schema ensure failed", error=str(e))

async def close_db() -> None:
    """Close database connections"""
    
    global engine, async_engine, async_read_engine
    
    # Dispose primary engine (support tests that patch `engine` only)
    if engine and engine is not async_engine:
        try:
            dispose_call = getattr(engine, "dispose", None)
            if dispose_call is not None:
                res = dispose_call()
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    await res
            logger.info("✅ Primary database connections closed (engine)")
        except Exception as e:
            logger.error("❌ Error closing primary database (engine)", error=str(e))
        finally:
            engine = None
    
    if async_engine:
        try:
            dispose_call = getattr(async_engine, "dispose", None)
            if dispose_call is not None:
                res = dispose_call()
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    await res
            logger.info("✅ Primary database connections closed")
        except Exception as e:
            logger.error("❌ Error closing primary database", error=str(e))
        finally:
            async_engine = None
    
    if async_read_engine and async_read_engine != async_engine:
        try:
            dispose_call = getattr(async_read_engine, "dispose", None)
            if dispose_call is not None:
                res = dispose_call()
                if asyncio.iscoroutine(res) or hasattr(res, "__await__"):
                    await res
            logger.info("✅ Read replica database connections closed")
        except Exception as e:
            logger.error("❌ Error closing read replica database", error=str(e))
        finally:
            async_read_engine = None


def get_async_session_factory() -> async_sessionmaker:
    """Get async session factory"""
    
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    return async_session_factory


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session with automatic cleanup"""
    
    session_factory = get_async_session_factory()
    
    # Create session directly so we control lifecycle in tests/mocks
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# Dependency for FastAPI route injection
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session injection (write operations)"""
    global async_session_factory
    # Lazy-initialize in test/dev to avoid manual init during e2e
    try:
        if async_session_factory is None and get_settings().ENVIRONMENT in ("test", "development"):
            await init_db()
    except Exception:
        # If init fails, propagate original error when requesting session
        pass
    async with get_async_session() as session:
        yield session


def get_async_read_session_factory() -> async_sessionmaker:
    """Get async session factory for read operations"""
    
    if async_read_session_factory is None:
        # Fallback to primary if no read replica
        return get_async_session_factory()
    
    return async_read_session_factory


@asynccontextmanager
async def get_async_read_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for read-only operations"""
    
    session_factory = get_async_read_session_factory()
    
    session = session_factory()
    try:
        yield session
    except Exception as e:
        logger.error("❌ Error in read session", error=str(e))
        raise
    finally:
        await session.close()


async def get_read_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for read-only database session injection"""
    
    async with get_async_read_session() as session:
        yield session

# Backward-compatible alias expected by some tests
# get_session should provide a write-capable session context manager
get_session = get_async_session


# Database event listeners for monitoring
# @event.listens_for(async_engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     """Set database connection parameters"""
#     
#     if hasattr(dbapi_connection, "set_isolation_level"):
#         # PostgreSQL specific settings
#         pass


# @event.listens_for(async_engine, "checkout")
# def receive_checkout(dbapi_connection, connection_record, connection_proxy):
#     """Monitor connection checkout"""
#     
#     logger.debug("📊 Database connection checked out")


# @event.listens_for(async_engine, "checkin")
# def receive_checkin(dbapi_connection, connection_record):
#     """Monitor connection checkin"""
#     
#     logger.debug("📊 Database connection checked in")


# Decorator for read-only operations
def read_only(func):
    """Decorator to mark functions that should use read replica"""
    func._read_only = True
    return func


# Utility functions for database operations
async def execute_query(query: str, params: dict = None, read_only: bool = False) -> list:
    """Execute raw SQL query
    
    Args:
        query: SQL query to execute
        params: Query parameters
        read_only: Whether to use read replica
    """
    
    session_context = get_async_read_session() if read_only else get_async_session()
    
    async with session_context as session:
        # SQLAlchemy 2.0 requires textual SQL to be wrapped with text()
        stmt = text(query) if isinstance(query, str) else query
        result = await session.execute(stmt, params or {})
        return result.fetchall()


async def check_database_health() -> dict:
    """Check database health and connection pool status"""
    
    try:
        async with get_async_session() as session:
            # Test query
            result = await session.execute(text("SELECT version(), current_database(), current_user"))
            db_info = result.fetchone()
            
            # Get connection pool stats
            pool = async_engine.pool
            
            return {
                "status": "healthy",
                "database": db_info[1] if db_info else "unknown",
                "user": db_info[2] if db_info else "unknown", 
                "version": db_info[0].split()[0] if db_info else "unknown",
                "pool": {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "overflow": pool.overflow(), 
                    "checked_out": pool.checkedout(),
                }
            }
            
    except Exception as e:
        logger.error("❌ Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Database initialization for development
async def create_tables():
    """Create all database tables (development only)"""
    
    settings = get_settings()
    
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Cannot create tables in production. Use migrations instead.")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("📊 Database tables created")


async def drop_tables():
    """Drop all database tables (development only)"""
    
    settings = get_settings()
    
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Cannot drop tables in production.")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("🗑️ Database tables dropped")


# Backward compatibility aliases for tests
get_session = get_db_session
init_database = init_db
close_database = close_db
