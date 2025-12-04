# PRD: RAG Configuration Settings Management

## Overview

Create a comprehensive settings interface that allows users to customize all retrieval, consolidation, and augmentation parameters for the RAG pipeline. Currently, these parameters are hard-coded across multiple modules. This PRD outlines the implementation to store configurations in a database, expose them via API, and provide a UI for management with support for multiple preset configurations.

## Problem Statement

Currently, RAG pipeline parameters (retrieval limits, RRF settings, entity boost, MMR lambda, consolidation thresholds, augmentation settings, etc.) are hard-coded in Python modules. Users cannot tune these parameters without modifying code, and there's no way to save different configurations for different use cases or experiment with parameter values.

## Goals

1. **Centralize Configuration**: Store all RAG parameters in a database table
2. **Flexible Presets**: Support multiple named configuration presets (like prompt templates)
3. **User-Friendly UI**: Provide intuitive settings interface with validation
4. **API-Driven**: Expose CRUD operations via REST API
5. **Future-Proof**: Design schema to support per-query configurations in the future
6. **Seamless Integration**: Update existing modules to pull from config instead of hard-coded defaults

## Non-Goals (Future Enhancements)

- Per-query configuration override (designed for but not implemented)
- A/B testing framework for configurations
- Configuration analytics/performance tracking
- Automatic parameter optimization

---

## Technical Specification

### 1. Database Schema

**Table Name**: `rag_config`

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique identifier |
| `preset_name` | `VARCHAR(100)` | `UNIQUE NOT NULL` | Human-readable preset name |
| `is_default` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Whether this is the default preset |
| `description` | `TEXT` | `NULL` | Optional description of preset purpose |
| `config` | `JSONB` | `NOT NULL` | Configuration parameters (see structure below) |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Last update timestamp |

**JSONB Structure** (`config` column):

```json
{
  "retrieval": {
    "dense_limit": 19,
    "lexical_limit": 5,
    "rrf_k": 50,
    "top_k_rrf": 75,
    "top_n_final": 17,
    "entity_boost": 0.05,
    "min_word_count": 150,
    "min_char_count": 250,
    "min_content_length": 750,
    "enrich_lines_above": 0,
    "enrich_lines_below": 13,
    "mmr_lambda": 0.7,
    "reranker_batch_size": 8,
    "reranker_max_length": 512
  },
  "consolidation": {
    "coverage_threshold": 0.5,
    "line_gap": 7,
    "min_content_length": 350,
    "enrich_from_md": true
  },
  "augmentation": {
    "top_n_contexts": 5
  }
}
```

**Constraints & Validation**:
- Only one preset can have `is_default = TRUE` at a time (enforced via trigger)
- At least one preset must exist
- Cannot delete the default preset without setting another as default

**Migration File**: `migrations/013_create_rag_config.sql`

**Indexes**:
- `CREATE INDEX idx_rag_config_preset_name ON rag_config(preset_name);`
- `CREATE INDEX idx_rag_config_is_default ON rag_config(is_default) WHERE is_default = TRUE;`

**Triggers**:
- `update_rag_config_updated_at()`: Auto-update `updated_at` timestamp on UPDATE
- `ensure_single_default_rag_config()`: Ensure only one preset has `is_default = TRUE`

### 2. Parameter Specifications

#### 2.1 Retrieval Parameters

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `dense_limit` | `int` | 19 | 1 | 100 | Max results per dense vector query |
| `lexical_limit` | `int` | 5 | 1 | 50 | Max results per lexical (BM25) query |
| `rrf_k` | `int` | 50 | 1 | 100 | RRF constant for rank fusion |
| `top_k_rrf` | `int` | 75 | 1 | 200 | Top candidates after RRF fusion |
| `top_n_final` | `int` | 17 | 1 | 50 | Final number of results after MMR |
| `entity_boost` | `float` | 0.05 | 0.0 | 0.5 | Score boost per entity match |
| `min_word_count` | `int` | 150 | 0 | 1000 | Minimum words in chunk (0 to disable) |
| `min_char_count` | `int` | 250 | 0 | 5000 | Minimum characters in chunk (0 to disable) |
| `min_content_length` | `int` | 750 | 0 | 5000 | Min content length before enrichment |
| `enrich_lines_above` | `int` | 0 | 0 | 50 | Lines to add above chunk when enriching |
| `enrich_lines_below` | `int` | 13 | 0 | 50 | Lines to add below chunk when enriching |
| `mmr_lambda` | `float` | 0.7 | 0.0 | 1.0 | MMR balance: relevance (1.0) vs diversity (0.0) |
| `reranker_batch_size` | `int` | 8 | 1 | 32 | Batch size for BGE reranker inference |
| `reranker_max_length` | `int` | 512 | 128 | 1024 | Max token length for reranker |

**Notes**:
- `dense_limit` × (num_queries) = total dense candidates
- `lexical_limit` × (num_queries) = total lexical candidates
- `top_k_rrf` must be ≥ `top_n_final`
- `mmr_lambda` = 1.0 means pure relevance (no diversity), 0.0 means pure diversity

#### 2.2 Consolidation Parameters

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `coverage_threshold` | `float` | 0.5 | 0.0 | 1.0 | % of parent coverage to replace with parent |
| `line_gap` | `int` | 7 | 0 | 50 | Max lines between chunks to merge them |
| `min_content_length` | `int` | 350 | 0 | 5000 | Min characters for final output inclusion |
| `enrich_from_md` | `bool` | `true` | - | - | Read content from markdown during consolidation |

**Notes**:
- `coverage_threshold` = 0.5 means if chunks cover 50%+ of parent, replace with parent
- `line_gap` = 0 means no merging (only exact adjacency)

#### 2.3 Augmentation Parameters

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `top_n_contexts` | `int` | 5 | 1 | 20 | Number of top contexts to include in prompt |

**Notes**:
- This is pulled from `clean_retrieval_context` after consolidation
- Contexts are sorted by score (descending)

### 3. Backend Implementation

#### 3.1 Database Model (`src/psychrag/data/models/rag_config.py`)

```python
from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..database import Base


class RagConfig(Base):
    """RAG configuration preset model."""

    __tablename__ = "rag_config"

    id = Column(Integer, primary_key=True)
    preset_name = Column(String(100), unique=True, nullable=False, index=True)
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    description = Column(Text, nullable=True)
    config = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    def __repr__(self):
        return f"<RagConfig(preset_name='{self.preset_name}', is_default={self.is_default})>"
```

#### 3.2 API Endpoints (`src/psychrag/api/routes/rag_config.py`)

**Base Path**: `/api/rag-config`

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/` | List all presets | - | `200: RagConfig[]` |
| `GET` | `/default` | Get default preset | - | `200: RagConfig` or `404` |
| `GET` | `/{preset_name}` | Get preset by name | - | `200: RagConfig` or `404` |
| `POST` | `/` | Create new preset | `RagConfigCreate` | `201: RagConfig` |
| `PUT` | `/{preset_name}` | Update preset | `RagConfigUpdate` | `200: RagConfig` |
| `PUT` | `/{preset_name}/set-default` | Set as default | - | `200: RagConfig` |
| `DELETE` | `/{preset_name}` | Delete preset | - | `204: No Content` or `400` |

**Schemas** (Pydantic):

```python
# Request schemas
class RagConfigCreate(BaseModel):
    preset_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: bool = False
    config: RagConfigParams  # Nested model with validation

class RagConfigUpdate(BaseModel):
    description: Optional[str] = None
    config: Optional[RagConfigParams] = None

class RagConfigParams(BaseModel):
    retrieval: RetrievalParams
    consolidation: ConsolidationParams
    augmentation: AugmentationParams

class RetrievalParams(BaseModel):
    dense_limit: int = Field(19, ge=1, le=100)
    lexical_limit: int = Field(5, ge=1, le=50)
    rrf_k: int = Field(50, ge=1, le=100)
    top_k_rrf: int = Field(75, ge=1, le=200)
    top_n_final: int = Field(17, ge=1, le=50)
    entity_boost: float = Field(0.05, ge=0.0, le=0.5)
    min_word_count: int = Field(150, ge=0, le=1000)
    min_char_count: int = Field(250, ge=0, le=5000)
    min_content_length: int = Field(750, ge=0, le=5000)
    enrich_lines_above: int = Field(0, ge=0, le=50)
    enrich_lines_below: int = Field(13, ge=0, le=50)
    mmr_lambda: float = Field(0.7, ge=0.0, le=1.0)
    reranker_batch_size: int = Field(8, ge=1, le=32)
    reranker_max_length: int = Field(512, ge=128, le=1024)

    @model_validator(mode='after')
    def validate_top_k_consistency(self):
        if self.top_k_rrf < self.top_n_final:
            raise ValueError("top_k_rrf must be >= top_n_final")
        return self

class ConsolidationParams(BaseModel):
    coverage_threshold: float = Field(0.5, ge=0.0, le=1.0)
    line_gap: int = Field(7, ge=0, le=50)
    min_content_length: int = Field(350, ge=0, le=5000)
    enrich_from_md: bool = True

class AugmentationParams(BaseModel):
    top_n_contexts: int = Field(5, ge=1, le=20)

# Response schema
class RagConfig(BaseModel):
    id: int
    preset_name: str
    is_default: bool
    description: Optional[str]
    config: RagConfigParams
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### 3.3 Config Loader Utility (`src/psychrag/utils/config_loader.py`)

```python
"""Utility to load RAG configuration from database."""

from typing import Optional
from sqlalchemy.orm import Session

from ..data.database import get_session
from ..data.models.rag_config import RagConfig


def get_default_config() -> dict:
    """Get default RAG configuration from database.

    Returns:
        Dict with retrieval, consolidation, and augmentation params.

    Raises:
        RuntimeError: If no default config exists in database.
    """
    with get_session() as session:
        config = session.query(RagConfig).filter(RagConfig.is_default == True).first()
        if not config:
            raise RuntimeError("No default RAG configuration found in database")
        return config.config


def get_config_by_name(preset_name: str) -> dict:
    """Get RAG configuration by preset name.

    Args:
        preset_name: Name of the preset to load.

    Returns:
        Dict with retrieval, consolidation, and augmentation params.

    Raises:
        ValueError: If preset not found.
    """
    with get_session() as session:
        config = session.query(RagConfig).filter(RagConfig.preset_name == preset_name).first()
        if not config:
            raise ValueError(f"RAG config preset '{preset_name}' not found")
        return config.config
```

#### 3.4 Update Existing Modules

**Files to Update**:
1. `src/psychrag/retrieval/retrieve.py` - Load retrieval params from config
2. `src/psychrag/augmentation/consolidate_context.py` - Load consolidation params from config
3. `src/psychrag/augmentation/augment.py` - Load augmentation params from config

**Pattern**:
```python
from psychrag.utils.config_loader import get_default_config

def retrieve(query_id: int, config_preset: Optional[str] = None, verbose: bool = False):
    # Load config
    config = get_default_config() if not config_preset else get_config_by_name(config_preset)
    retrieval_params = config["retrieval"]

    # Use params
    dense_limit = retrieval_params["dense_limit"]
    lexical_limit = retrieval_params["lexical_limit"]
    # ... etc
```

#### 3.5 Database Initialization

Update `src/psychrag/data/init_db.py`:

```python
from .models.rag_config import RagConfig  # noqa: F401

# Add function
def create_default_rag_config(verbose: bool = False) -> None:
    """Create default RAG configuration preset if none exists."""
    with get_session() as session:
        existing = session.query(RagConfig).first()
        if existing:
            if verbose:
                print("RAG config presets already exist")
            return

        default_config = RagConfig(
            preset_name="Default",
            is_default=True,
            description="Default RAG configuration with balanced settings",
            config={
                "retrieval": {
                    "dense_limit": 19,
                    "lexical_limit": 5,
                    "rrf_k": 50,
                    "top_k_rrf": 75,
                    "top_n_final": 17,
                    "entity_boost": 0.05,
                    "min_word_count": 150,
                    "min_char_count": 250,
                    "min_content_length": 750,
                    "enrich_lines_above": 0,
                    "enrich_lines_below": 13,
                    "mmr_lambda": 0.7,
                    "reranker_batch_size": 8,
                    "reranker_max_length": 512
                },
                "consolidation": {
                    "coverage_threshold": 0.5,
                    "line_gap": 7,
                    "min_content_length": 350,
                    "enrich_from_md": True
                },
                "augmentation": {
                    "top_n_contexts": 5
                }
            }
        )
        session.add(default_config)
        session.commit()

        if verbose:
            print("Created default RAG config preset")

# Update init_database()
def init_database(verbose: bool = False) -> None:
    create_database_and_user(verbose=verbose)
    enable_pgvector_extension(verbose=verbose)
    create_tables(verbose=verbose)
    create_vector_indexes(verbose=verbose)
    create_fulltext_search(verbose=verbose)
    create_prompt_meta_table(verbose=verbose)
    create_default_rag_config(verbose=verbose)  # Add this line
```

### 4. Frontend Implementation

#### 4.1 Settings Page Tab

Update `psychrag_ui/src/app/settings/page.tsx`:

Add new tab to the `TabsList`:
```tsx
<TabsTrigger value="rag">RAG Settings</TabsTrigger>
```

Add new `TabsContent`:
```tsx
<TabsContent value="rag" className="mt-4">
  <RagConfigTab />
</TabsContent>
```

#### 4.2 RAG Config Component

Create `psychrag_ui/src/components/settings/rag-config-tab.tsx`:

**Features**:
- **Preset Selector**: Dropdown to select/switch between presets
- **Preset Management**: Create, rename, delete, set default
- **Three Collapsible Sections**: Retrieval, Consolidation, Augmentation
- **Parameter Inputs**: Number inputs, sliders, toggles with validation
- **Save/Reset**: Save changes, reset to last saved, reset to defaults
- **Active Indicator**: Show which preset is default

**UI Structure**:
```
┌─────────────────────────────────────────────────────────┐
│ RAG Configuration Presets                               │
│                                                         │
│ ┌─────────────────┐  [+ New Preset]  [Set as Default] │
│ │ Preset: Default ▾│                                   │
│ └─────────────────┘                                    │
│                                                         │
│ ▼ Retrieval Parameters                                 │
│   ┌────────────────────────────────────────────┐      │
│   │ Dense Limit: [19    ] (1-100)              │      │
│   │ Lexical Limit: [5     ] (1-50)             │      │
│   │ RRF K: [50    ] (1-100)                    │      │
│   │ Top K RRF: [75    ] (1-200)                │      │
│   │ Top N Final: [17    ] (1-50)               │      │
│   │ Entity Boost: [0.05  ] (0.0-0.5)           │      │
│   │ MMR Lambda: [0.7   ] ────────────────      │      │
│   │             Relevance ◄──────────► Diversity│      │
│   │ ... (other parameters)                      │      │
│   └────────────────────────────────────────────┘      │
│                                                         │
│ ▶ Consolidation Parameters                             │
│                                                         │
│ ▶ Augmentation Parameters                              │
│                                                         │
│ [Save Changes]  [Reset]  [Delete Preset]               │
└─────────────────────────────────────────────────────────┘
```

**Component Outline**:

```tsx
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Select } from "@/components/ui/select";

interface RagConfigParams {
  retrieval: RetrievalParams;
  consolidation: ConsolidationParams;
  augmentation: AugmentationParams;
}

export function RagConfigTab() {
  const [presets, setPresets] = useState<RagConfig[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [config, setConfig] = useState<RagConfigParams | null>(null);

  // Fetch presets on mount
  // Render preset selector
  // Render three accordion sections
  // Handle save, reset, delete, set default
}
```

**Parameter Input Components**:
- Number inputs with min/max validation
- Sliders for float parameters (mmr_lambda, entity_boost, coverage_threshold)
- Toggle switches for boolean parameters (enrich_from_md)
- Tooltips with parameter descriptions
- Real-time validation feedback

#### 4.3 Type Definitions

Create `psychrag_ui/src/types/rag-config.ts`:

```typescript
export interface RagConfig {
  id: number;
  preset_name: string;
  is_default: boolean;
  description: string | null;
  config: RagConfigParams;
  created_at: string;
  updated_at: string;
}

export interface RagConfigParams {
  retrieval: RetrievalParams;
  consolidation: ConsolidationParams;
  augmentation: AugmentationParams;
}

export interface RetrievalParams {
  dense_limit: number;
  lexical_limit: number;
  rrf_k: number;
  top_k_rrf: number;
  top_n_final: number;
  entity_boost: number;
  min_word_count: number;
  min_char_count: number;
  min_content_length: number;
  enrich_lines_above: number;
  enrich_lines_below: number;
  mmr_lambda: number;
  reranker_batch_size: number;
  reranker_max_length: number;
}

export interface ConsolidationParams {
  coverage_threshold: number;
  line_gap: number;
  min_content_length: number;
  enrich_from_md: boolean;
}

export interface AugmentationParams {
  top_n_contexts: number;
}

// Validation constraints
export const PARAM_CONSTRAINTS = {
  retrieval: {
    dense_limit: { min: 1, max: 100, default: 19 },
    lexical_limit: { min: 1, max: 50, default: 5 },
    rrf_k: { min: 1, max: 100, default: 50 },
    top_k_rrf: { min: 1, max: 200, default: 75 },
    top_n_final: { min: 1, max: 50, default: 17 },
    entity_boost: { min: 0.0, max: 0.5, default: 0.05, step: 0.01 },
    min_word_count: { min: 0, max: 1000, default: 150 },
    min_char_count: { min: 0, max: 5000, default: 250 },
    min_content_length: { min: 0, max: 5000, default: 750 },
    enrich_lines_above: { min: 0, max: 50, default: 0 },
    enrich_lines_below: { min: 0, max: 50, default: 13 },
    mmr_lambda: { min: 0.0, max: 1.0, default: 0.7, step: 0.01 },
    reranker_batch_size: { min: 1, max: 32, default: 8 },
    reranker_max_length: { min: 128, max: 1024, default: 512 },
  },
  consolidation: {
    coverage_threshold: { min: 0.0, max: 1.0, default: 0.5, step: 0.01 },
    line_gap: { min: 0, max: 50, default: 7 },
    min_content_length: { min: 0, max: 5000, default: 350 },
    enrich_from_md: { default: true },
  },
  augmentation: {
    top_n_contexts: { min: 1, max: 20, default: 5 },
  },
} as const;
```

---

## Implementation Plan

### Phase 1: Database & Backend (Week 1)

1. ✅ Create migration `013_create_rag_config.sql`
2. ✅ Create SQLAlchemy model `RagConfig`
3. ✅ Update `init_db.py` to create table and default preset
4. ✅ Create API routes and schemas
5. ✅ Create config loader utility
6. ✅ Write unit tests for API endpoints

### Phase 2: Module Integration (Week 2)

1. ✅ Update `retrieve.py` to use config loader
2. ✅ Update `consolidate_context.py` to use config loader
3. ✅ Update `augment.py` to use config loader
4. ✅ Add optional `config_preset` parameter to all functions
5. ✅ Write integration tests

### Phase 3: Frontend (Week 3)

1. ✅ Create TypeScript types
2. ✅ Create `RagConfigTab` component
3. ✅ Implement preset selector and management
4. ✅ Implement three accordion sections with parameter inputs
5. ✅ Add validation and error handling
6. ✅ Test UI end-to-end

### Phase 4: Documentation & Polish (Week 4)

1. ✅ Update user documentation
2. ✅ Add inline help tooltips in UI
3. ✅ Create example presets (Fast, Balanced, Thorough)
4. ✅ Final testing and bug fixes

---

## Success Metrics

1. **Usability**: Users can create/edit/save presets without technical knowledge
2. **Validation**: Invalid configurations are prevented with clear error messages
3. **Performance**: No performance degradation from config loading
4. **Flexibility**: Support 3+ different presets for different use cases
5. **Adoption**: 80%+ of queries use custom configs within 2 weeks of launch

---

## Open Questions

1. Should we expose intent bias parameters (currently in `INTENT_PREFERENCES` dict)?
2. Should we version configs for rollback capability?
3. Do we need a "test configuration" feature to run queries with temporary settings?

---

## Appendix: Migration SQL

See `migrations/013_create_rag_config.sql` for full implementation.

**Key sections**:
- Table creation
- Indexes
- Trigger for `updated_at`
- Trigger to enforce single default
- Insert default preset
- Comments

---

## References

- [retrieval.md](./retrieval.md) - Retrieval pipeline documentation
- [augmentation.md](./augmentation.md) - Augmentation pipeline documentation
- `src/psychrag/retrieval/retrieve.py` - Current retrieval implementation
- `src/psychrag/augmentation/consolidate_context.py` - Current consolidation implementation
- `src/psychrag/augmentation/augment.py` - Current augmentation implementation
