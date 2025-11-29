COMPLETE

# T01: Database schema and migration for prompt templates

## Context

- **PRD**: [templates_prd.md](templates_prd.md)
- **PRD Section**: Lines 16-21 (model and table creation, migration requirements)
- **User Value**: Establishes the foundational data model for storing versioned prompt templates, enabling the system to manage multiple template versions per function with user-controlled activation.

## Outcome

The database has a `prompt_templates` table that supports versioned storage of LangChain PromptTemplate strings, with automatic version incrementing per function tag. The migration script creates the table and seeds it with V1 templates extracted from the existing codebase as the initial versions.

## Scope

**In scope:**
- Create `prompt_templates` table with fields for function tag, version, title, template content, active flag, and timestamps
- Design schema to support automatic version incrementing per function tag
- Create SQL migration file in `/migrations/` folder following existing naming convention (e.g., `011_create_prompt_templates.sql`)
- Seed migration with INSERT statements for V1 templates from 4 existing functions:
  - Query Expansion (from `src/psychrag/retrieval/query_expansion.py`)
  - RAG Augmented Prompt (from `src/psychrag/augmentation/augment.py`)
  - Vectorization Suggestions (from `src/psychrag/chunking/suggested_chunks.py`)
  - Heading Hierarchy Corrections (from `src/psychrag/sanitization/suggest_heading_changes.py`)
- Extract prompt strings and convert to LangChain PromptTemplate format with variables
- Create SQLAlchemy model class in `/src/psychrag/data/models/` for ORM access
- Update `/src/psychrag/data/init_db.py`so that table is created on fresh install -- migration sql query will be run manually

**Out of scope:**
- API endpoints (handled in T02)
- UI implementation (handled in T03)
- Integration with existing functions (handled in T04)
- Migration rollback scripts (follow existing project pattern)

## Implementation plan

### Backend

#### 1. Database schema design

Create table `prompt_templates` with the following columns:

```sql
CREATE TABLE prompt_templates (
    id SERIAL PRIMARY KEY,
    function_tag VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    template_content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(function_tag, version),
    CHECK(version > 0)
);

CREATE INDEX idx_prompt_templates_function_tag ON prompt_templates(function_tag);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(function_tag, is_active);
```

**Design decisions:**
- `function_tag`: Simple string identifier (e.g., `query_expansion`, `rag_augmentation`)
- `version`: Integer starting at 1, auto-incremented per function_tag
- `is_active`: Only ONE template per function_tag should have `is_active=TRUE` at any time
- `UNIQUE(function_tag, version)`: Prevents duplicate versions
- Indexes on `function_tag` and `(function_tag, is_active)` for efficient lookups

#### 2. Extract existing prompts and convert to PromptTemplate format

For each of the 4 functions, extract the prompt-building logic and identify variables:

**Query Expansion** (`src/psychrag/retrieval/query_expansion.py:56-143`):
- Function: `generate_expansion_prompt(query: str, n: int = 3) -> str`
- Variables: `{query}`, `{n}`
- Extract the f-string template and convert to PromptTemplate format
- Title: "Query Expansion - Multi-Query Expansion (MQE) and HyDE"

**RAG Augmented Prompt** (`src/psychrag/augmentation/augment.py:160-285`):
- Function: `generate_augmented_prompt(query_id: int, top_n: int = 5) -> str`
- Variables: `{intent}`, `{entities_str}`, `{context_blocks}`, `{user_question}`
- Extract the f-string from lines 205-283
- Title: "RAG Augmented Prompt - Context Integration"

**Vectorization Suggestions** (`src/psychrag/chunking/suggested_chunks.py:43-165`):
- Function: `_build_prompt(titles_content: str, bib_info: BibliographicInfo | None) -> str`
- Variables: `{bib_section}`, `{titles_content}`, `{n}` (potentially)
- Extract the prompt from lines 69-165
- Title: "Vectorization Suggestions - Heading Analysis"

**Heading Hierarchy Corrections** (`src/psychrag/sanitization/suggest_heading_changes.py:203-328`):
- Function: `_build_prompt(title: str, authors: str, toc: list, titles_codeblock: str) -> str`
- Variables: `{title}`, `{authors}`, `{toc_text}`, `{titles_codeblock}`
- Extract the prompt from lines 219-328
- Title: "Heading Hierarchy Corrections - ToC Alignment"

**Conversion strategy:**
- Replace f-string interpolations (`{variable}`) with PromptTemplate placeholders (keep same syntax)
- Store as plain text strings in the database
- Ensure all literal braces are doubled (`{{` and `}}`) if needed for PromptTemplate compatibility

#### 3. Create migration file

File: `/migrations/010_create_prompt_templates.sql`

Structure:
```sql
-- Create table
CREATE TABLE prompt_templates (...);
CREATE INDEX ...;

-- Seed V1 templates
INSERT INTO prompt_templates (function_tag, version, title, template_content, is_active, created_at, updated_at)
VALUES
    ('query_expansion', 1, 'Query Expansion - Multi-Query Expansion (MQE) and HyDE',
     'You are a query expansion assistant for a psychology...{query}...{n}...',
     TRUE, NOW(), NOW()),
    ('rag_augmentation', 1, 'RAG Augmented Prompt - Context Integration',
     'You are an academic assistant...{context_blocks}...{user_question}...',
     TRUE, NOW(), NOW()),
    ('vectorization_suggestions', 1, 'Vectorization Suggestions - Heading Analysis',
     'You are analyzing a document''s heading structure...{titles_content}...',
     TRUE, NOW(), NOW()),
    ('heading_hierarchy', 1, 'Heading Hierarchy Corrections - ToC Alignment',
     'You are an expert at analyzing document structure...{title}...{authors}...',
     TRUE, NOW(), NOW());
```

**Notes:**
- Use single quotes for SQL strings, escape internal quotes with `''`
- Set `is_active=TRUE` for all V1 templates (they become the default active versions)
- Use `NOW()` for timestamps

#### 4. Create SQLAlchemy model

File: `/src/psychrag/data/models/prompt_template.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import validates
from ..database import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True)
    function_tag = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    template_content = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_prompt_templates_function_tag', 'function_tag'),
        Index('idx_prompt_templates_active', 'function_tag', 'is_active'),
    )

    @validates('version')
    def validate_version(self, key, value):
        if value <= 0:
            raise ValueError("Version must be greater than 0")
        return value

    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, function_tag='{self.function_tag}', version={self.version}, active={self.is_active})>"
```

#### 5. Update init_db.py

File: `/src/psychrag/data/init_db.py`

Add import:
```python
from .models.prompt_template import PromptTemplate  # noqa: F401
```

This ensures the model is registered with SQLAlchemy's Base metadata.

**Note**: The migration SQL file will be run manually or via a migration runner. The existing `init_db.py` pattern appears to use `Base.metadata.create_all()` which creates tables from models, but migrations should be applied separately. Verified this is the case.

#### 6. Validation and constraints

Ensure business logic constraints:
- **One active template per function**: This will be enforced at the API level (T02), not via DB constraint (would be complex with triggers)
- **Auto-increment version**: Calculate `MAX(version) + 1` for a given `function_tag` when creating new versions (handled in T02)
- **Non-negative version**: Enforced via CHECK constraint in schema

### Other / cross-cutting

**Migration execution:**
- Follow existing project pattern for running migrations
- If using manual SQL execution: Document the command in ticket or README
- If using Alembic or similar: Create Alembic migration file instead of raw SQL

**Documentation:**
- Add comments to migration file explaining the schema
- Document the function tags and their meanings
- Note that V1 templates are extracted from existing code

## Unit tests

**Target**: `tests/unit/test_prompt_template_model.py`

Create unit tests for the SQLAlchemy model:

1. **Test model creation**:
   - `test_create_prompt_template()`: Create a PromptTemplate instance and verify all fields
   - `test_default_values()`: Verify `is_active` defaults to `FALSE`, timestamps auto-populate

2. **Test validation**:
   - `test_version_validation_positive()`: Version must be > 0
   - `test_version_validation_zero()`: Version = 0 raises ValueError
   - `test_version_validation_negative()`: Version < 0 raises ValueError

3. **Test database constraints** (integration-style, requires test DB):
   - `test_unique_constraint()`: Cannot insert duplicate (function_tag, version)
   - `test_function_tag_required()`: function_tag is NOT NULL
   - `test_template_content_required()`: template_content is NOT NULL

4. **Test queries**:
   - `test_query_by_function_tag()`: Retrieve all templates for a function_tag
   - `test_query_active_template()`: Retrieve the active template for a function_tag
   - `test_query_specific_version()`: Retrieve a specific version

**Test framework**: Use existing test setup (appears to be pytest based on `tests/unit/test_*.py` pattern)

**Test database**: Use a test database or SQLite in-memory DB for unit tests

**Fixtures**:
```python
@pytest.fixture
def sample_templates(session):
    """Create sample templates for testing."""
    templates = [
        PromptTemplate(
            function_tag="query_expansion",
            version=1,
            title="Test Query Expansion V1",
            template_content="Test template with {query}",
            is_active=True
        ),
        PromptTemplate(
            function_tag="query_expansion",
            version=2,
            title="Test Query Expansion V2",
            template_content="Updated template with {query}",
            is_active=False
        ),
    ]
    session.add_all(templates)
    session.commit()
    return templates
```

## Manual test plan

After implementing this ticket:

1. **Verify migration execution**:
   - Run the migration script against a test database
   - Verify table `prompt_templates` exists with correct schema
   - Verify 4 rows are inserted (one per function tag, all V1, all active)

2. **Verify data integrity**:
   - Query: `SELECT * FROM prompt_templates;`
   - Verify each template has correct `function_tag`, `version=1`, `is_active=TRUE`
   - Verify `template_content` contains the extracted prompts with variables

3. **Test constraints**:
   - Attempt to insert duplicate (function_tag, version): Should fail with UNIQUE constraint error
   - Attempt to insert version=0: Should fail with CHECK constraint error
   - Attempt to insert NULL function_tag: Should fail with NOT NULL constraint error

4. **Test ORM access**:
   ```python
   from psychrag.data.database import get_session
   from psychrag.data.models.prompt_template import PromptTemplate

   with get_session() as session:
       # Query all templates
       all_templates = session.query(PromptTemplate).all()
       print(f"Total templates: {len(all_templates)}")  # Should be 4

       # Query active template for query_expansion
       active = session.query(PromptTemplate).filter(
           PromptTemplate.function_tag == "query_expansion",
           PromptTemplate.is_active == True
       ).first()
       print(f"Active query_expansion: v{active.version} - {active.title}")
   ```

5. **Verify LangChain PromptTemplate compatibility**:
   ```python
   from langchain_core.prompts import PromptTemplate as LangChainPromptTemplate

   # Test that stored templates can be loaded as LangChain PromptTemplates
   with get_session() as session:
       template = session.query(PromptTemplate).filter(
           PromptTemplate.function_tag == "query_expansion"
       ).first()

       # Create LangChain PromptTemplate from stored content
       lc_template = LangChainPromptTemplate.from_template(template.template_content)

       # Test formatting with variables
       result = lc_template.format(query="test query", n=3)
       print("Formatted template:", result[:100])  # Should contain "test query" and "3"
   ```

## Dependencies and sequencing

**Must be completed before:**
- T02 (Backend API endpoints) - requires the table and model
- T04 (Integration with existing functions) - requires the table and seeded data

**Can be done in parallel with:**
- T03 (Settings UI) - frontend work doesn't block on this

**No blockers** - this is the foundation ticket

## Clarifications and assumptions

### Assumptions made:

1. **Migration strategy**: Assuming SQL migration files are run manually or via a dedicated migration runner (following pattern from existing `/migrations/*.sql` files)

2. **LangChain PromptTemplate format**: Storing templates as strings with `{variable}` syntax, compatible with `PromptTemplate.from_template()` - **CLARIFY**: Should we validate this format on INSERT, or rely on API validation?

3. **Active template enforcement**: Only enforcing "one active template per function" at the application level (API), not via database triggers - **CLARIFY**: Is this acceptable, or do we need DB-level enforcement?

4. **Version numbering**: Versions start at 1 and increment by 1 for each new version - **CLARIFY**: Any special versioning scheme needed (e.g., semantic versioning)?

5. **Template extraction**: Extracting full prompt strings from existing code as-is, converting f-strings to template format - **CLARIFY**: Should V1 templates be exact copies, or can we clean them up / improve formatting?

6. **Existing code as fallback**: V1 templates in DB should match the hardcoded prompts in existing code exactly, so fallback behavior is identical - **CONFIRM**: This is critical for T04 integration

7. **Function tags**: Using snake_case for function tags:
   - `query_expansion`
   - `rag_augmentation`
   - `vectorization_suggestions`
   - `heading_hierarchy`

   **CLARIFY**: Are these the correct canonical tags?

8. **Bib_section handling**: For vectorization_suggestions, the `bib_section` variable is conditionally built - **CLARIFY**: Should the template include placeholder logic, or should this be pre-processed before formatting?

### Blocking questions:

**NONE** - Can proceed with implementation based on assumptions above. Verify assumptions in code review.

---

**Before implementing, review the Clarifications and assumptions section. If any assumption is incorrect or any blocking item is unclear, get explicit answers or update the ticket accordingly before writing code.**
