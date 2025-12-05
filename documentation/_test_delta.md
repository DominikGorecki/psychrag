# Implementation Plan: Convert Unit Tests to Pure Mocked Tests

## Overview

Convert all database-dependent unit tests in `tests/unit/` to use pure mocks instead of real SQLite databases. Remove the `engine()` and `session()` fixtures from `tests/conftest.py`. Document tests that require real database behavior as future integration tests.

## Goals

1. **Zero database dependencies** in unit tests - no SQLite or PostgreSQL
2. **Fast test execution** - full unit suite runs in <10 seconds
3. **Pure unit testing** - test business logic, not database behavior
4. **Clear documentation** - identify what needs integration testing

## Mocking Strategy

### What Gets Mocked

**SQLAlchemy Session Operations:**
- `session.add()`, `session.commit()`, `session.rollback()`
- `session.query()` - return controlled test data
- `session.delete()`, `session.refresh()`, `session.flush()`
- Context managers: `get_session()`, `SessionLocal()`

**Query Chain Operations (must be chainable):**
- `.filter()`, `.filter_by()`, `.order_by()`, `.limit()`
- `.all()` - returns list of objects
- `.first()` - returns single object or None
- `.count()` - returns integer

**Model Instances:**
- Create as plain Python objects or MagicMock
- Set attributes directly (no ORM behavior needed)

## Test Classification

### Pure Unit Tests (Convert to Mocks) - 16 Files

These test business logic, not database behavior:

1. **test_work_model.py** - Model attributes, `__repr__`, field assignment
2. **test_chunk_model.py** - Model logic, relationships (exclude CASCADE tests)
3. **test_query_model.py** - Model logic, JSON handling (exclude constraint tests)
4. **test_prompt_template_model.py** - Template model logic
5. **test_prompt_meta_model.py** - Metadata model logic
6. **test_result_model.py** - Result model logic
7. **test_io_file_model.py** - File model logic
8. **test_database.py** - Session context manager logic
9. **test_seed_templates.py** - Template seeding logic (already well-mocked)
10. **test_rag_config_db.py** - Config database operations
11. **test_rag_config_loader.py** - Config loading logic
12. **test_template_loader.py** - Template loading logic
13. **test_templates_api.py** - API endpoint logic
14. **test_retrieve.py** - Retrieval algorithms (RRF, MMR, similarity)
15. **test_query_embeddings.py** - Embedding logic (already well-mocked)
16. **test_init_db.py** - Keep mocks, document integration needs

### Integration Tests Needed (Document for Future)

Tests that require real database and should be removed from unit tests:

**A. CASCADE Delete Tests:**
- Tests that verify database-level CASCADE behavior
- Example: `test_cascade_delete_from_work`, `test_cascade_delete_from_parent`

**B. Foreign Key Constraint Tests:**
- Tests that expect `IntegrityError` for FK violations
- Example: `test_foreign_key_constraint_work`

**C. NOT NULL Constraint Tests:**
- Tests that expect `IntegrityError` for required fields
- Example: `test_work_id_required`, `test_level_required`

**D. PostgreSQL-Specific Features:**
- pgvector similarity search (`_dense_search()`)
- Full-text search with tsvector (`_lexical_search()`)
- JSONB storage behavior
- Vector type storage

**E. Database Initialization:**
- Actual database creation
- Table schema creation
- Health check connectivity

## Implementation Approach

### Phase 1: Foundation

**1. Create `tests/unit/mock_helpers.py`**

Reusable mock utilities for all tests:

```python
"""Mock helpers for unit tests without database."""
from unittest.mock import MagicMock
import pytest

@pytest.fixture
def mock_session():
    """Mock database session for unit tests."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()

    # Chainable query operations
    mock_query = MagicMock()
    mock_query.filter = MagicMock(return_value=mock_query)
    mock_query.filter_by = MagicMock(return_value=mock_query)
    mock_query.all = MagicMock(return_value=[])
    mock_query.first = MagicMock(return_value=None)
    mock_query.count = MagicMock(return_value=0)
    session.query = MagicMock(return_value=mock_query)

    return session

def create_mock_query_chain(return_data=None, return_first=None):
    """Create chainable mock query."""
    if return_data is None:
        return_data = []
    mock_query = MagicMock()
    mock_query.filter = MagicMock(return_value=mock_query)
    mock_query.filter_by = MagicMock(return_value=mock_query)
    mock_query.order_by = MagicMock(return_value=mock_query)
    mock_query.all = MagicMock(return_value=return_data)
    mock_query.first = MagicMock(return_value=return_first)
    return mock_query

def create_mock_work(id=1, title="Test Work", **kwargs):
    """Create mock Work instance."""
    work = MagicMock()
    work.id = id
    work.title = title
    work.authors = kwargs.get('authors', 'Test Author')
    return work

def create_mock_chunk(id=1, work_id=1, level="H1", content="Test", **kwargs):
    """Create mock Chunk instance."""
    chunk = MagicMock()
    chunk.id = id
    chunk.work_id = work_id
    chunk.level = level
    chunk.content = content
    chunk.vector_status = kwargs.get('vector_status', 'no_vec')
    return chunk
```

**2. Create `documentation/integration-tests-needed.md`**

Document all tests removed from unit tests that need integration testing:

```markdown
# Integration Tests Needed

## Criteria for Integration Tests

A test needs integration testing if it:
- Verifies database constraints (FK, NOT NULL, UNIQUE)
- Tests CASCADE DELETE at database level
- Tests PostgreSQL features (pgvector, tsvector, JSONB)
- Tests actual SQL query execution
- Tests database initialization/migrations

## Tests Requiring Integration

### CASCADE Delete Tests
- `test_chunk_model.py::test_cascade_delete_from_work`
- `test_chunk_model.py::test_cascade_delete_from_parent`

### Foreign Key Constraint Tests
- `test_chunk_model.py::test_foreign_key_constraint_work`
- `test_chunk_model.py::test_foreign_key_constraint_parent`
- Similar tests across all model files

### NOT NULL Constraint Tests
- All `test_[field]_required` tests that expect IntegrityError
- Found in: test_chunk_model.py, test_query_model.py, test_work_model.py, etc.

### PostgreSQL-Specific Features
- pgvector similarity search operations
- Full-text search with tsvector/tsquery
- JSONB storage and query operations

### Database Initialization
- `test_init_db.py` - actual database creation
- `test_db_health_check.py` - real connectivity tests

## Implementation Guide

```python
# tests/integration/conftest.py
@pytest.fixture(scope="session")
def integration_engine():
    return create_engine(TEST_DATABASE_URL)

@pytest.fixture
def integration_session(integration_engine):
    connection = integration_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```
```

### Phase 2: Convert Model Tests

**3. Convert `test_work_model.py` (Simplest Example)**

Before:
```python
def test_create_work_basic(self, session):
    work = Work(title="Test", authors="Author")
    session.add(work)
    session.commit()
    assert work.id is not None
```

After:
```python
def test_create_work_basic():
    work = Work(title="Test", authors="Author")
    assert work.title == "Test"
    assert work.authors == "Author"
```

**4. Convert `test_chunk_model.py` (Most Complex)**

Changes:
- Remove `session` fixture usage
- Create model instances directly
- Mock session operations for CRUD tests
- **Remove** CASCADE tests → document in integration-tests-needed.md
- **Remove** FK constraint tests → document in integration-tests-needed.md
- **Remove** NOT NULL tests → document in integration-tests-needed.md

Example conversion:
```python
# BEFORE: TestChunkCreation
def test_create_chunk_basic(self, session):
    work = Work(title="Test")
    session.add(work)
    session.commit()
    chunk = Chunk(work_id=work.id, level="H1", content="Chapter 1")
    session.add(chunk)
    session.commit()
    assert chunk.id is not None

# AFTER: TestChunkCreation
def test_create_chunk_basic():
    chunk = Chunk(
        work_id=1,
        level="H1",
        content="Chapter 1",
        start_line=1,
        end_line=10,
        vector_status="no_vec"
    )
    assert chunk.level == "H1"
    assert chunk.content == "Chapter 1"
    assert chunk.work_id == 1
```

**5. Convert `test_query_model.py`**

Focus on JSON/Vector fields as plain Python data:
```python
def test_expanded_queries_json():
    query = Query(
        original_query="Test",
        expanded_queries=["Q1", "Q2", "Q3"]
    )
    assert query.expanded_queries == ["Q1", "Q2", "Q3"]
    assert isinstance(query.expanded_queries, list)
```

**6-9. Convert remaining model tests:**
- `test_prompt_template_model.py`
- `test_prompt_meta_model.py`
- `test_result_model.py`
- `test_io_file_model.py`

Follow same pattern: create instances directly, mock session operations.

### Phase 3: Convert Infrastructure Tests

**10. Convert `test_database.py`**

Mock `SessionLocal` and test context manager logic:
```python
@patch("psychrag.data.database.SessionLocal")
def test_session_yields_and_closes(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    with get_session() as session:
        assert session == mock_session

    mock_session.close.assert_called_once()

@patch("psychrag.data.database.SessionLocal")
def test_session_rollback_on_exception(mock_session_local):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session

    with pytest.raises(ValueError):
        with get_session() as session:
            raise ValueError("Test error")

    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()
```

**11. Convert `test_init_db.py`**

Mock engine, connection, and execution. Document actual DB creation as integration test.

**12. Convert `test_db_health_check.py`**

Mock engine and connection. Document real connectivity tests as integration tests.

### Phase 4: Convert Configuration Tests

**13. Verify `test_seed_templates.py`**
Already well-mocked - verify no database fixture usage.

**14-16. Convert config tests:**
- `test_rag_config_db.py` - Mock session queries
- `test_rag_config_loader.py` - Mock file and session operations
- `test_template_loader.py` - Mock file and session operations

### Phase 5: Convert API & Retrieval Tests

**17. Convert `test_templates_api.py`**

Mock session for FastAPI dependency override:
```python
@pytest.fixture
def mock_session():
    session = MagicMock()
    mock_query = create_mock_query_chain(return_data=[])
    session.query.return_value = mock_query
    return session

@pytest.fixture
def client(mock_session):
    def override_get_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
```

**18. Complete `test_retrieve.py`**

Already mostly mocked - verify no remaining session fixture usage. Mock any direct database queries.

**19. Verify `test_query_embeddings.py`**

Already well-mocked - verify no database fixture usage.

### Phase 6: Cleanup

**20. Remove fixtures from `tests/conftest.py`**

Delete:
- `engine()` fixture (lines 20-77)
- `session()` fixture (lines 80-92)
- All SQLite table creation code
- All database-related imports

Keep:
- Any non-database fixtures (if present)
- Test configuration

**21. Update integration tests documentation**

Complete `documentation/integration-tests-needed.md` with all removed tests catalogued by category.

### Phase 7: Validation

**22. Run full test suite:**
```bash
pytest tests/unit/ -v
```

**23. Verify success criteria:**
- Execution time <10 seconds
- 100% pass rate
- No SQLite connections
- No database files created

## Critical Files to Modify

1. **tests/unit/mock_helpers.py** (NEW) - Reusable mock fixtures
2. **tests/conftest.py** (MODIFY) - Remove database fixtures
3. **documentation/integration-tests-needed.md** (NEW) - Document removed tests
4. **tests/unit/test_chunk_model.py** (MODIFY) - Most complex conversion
5. **tests/unit/test_query_model.py** (MODIFY) - JSON/Vector handling
6. **tests/unit/test_database.py** (MODIFY) - Session context manager
7. **tests/unit/test_retrieve.py** (MODIFY) - Complete retrieval mocking
8. **tests/unit/test_templates_api.py** (MODIFY) - API dependency mocking
9. **tests/unit/test_work_model.py** (MODIFY) - Simplest example
10. **tests/unit/test_init_db.py** (MODIFY) - Database initialization

Plus 11 additional model/config test files following established patterns.

## Success Criteria

1. **Zero database dependencies** - no create_engine() calls in unit tests
2. **Fast execution** - <10 seconds for full unit suite
3. **100% pass rate** - all tests passing
4. **Complete documentation** - all removed tests documented
5. **Clean separation** - clear unit vs integration test boundaries

## Benefits

- **Fast CI/CD** - unit tests run quickly without database setup
- **Reliable tests** - no database connection failures
- **True unit testing** - test logic, not database behavior
- **Clear coverage** - know what needs integration testing

