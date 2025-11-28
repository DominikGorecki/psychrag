# Breadcrumb Refactoring Plan

## Overview

Refactor the heading breadcrumb system to store breadcrumbs in a dedicated database column instead of embedding them in chunk content. This will:
- Improve data separation and clarity
- Enable flexible breadcrumb presentation in UI
- Maintain breadcrumb context for retrieval
- Require re-vectorization of all existing chunks

## Current State Analysis

### How Breadcrumbs Work Today

1. **Creation** (`content_chunking.py`):
   - Breadcrumbs are built from markdown heading structure
   - Format: `"H1 > H2 > H3"`
   - **Embedded at the start of chunk.content**: `"{breadcrumb}\n{actual_content}"`
   - Breadcrumbs count against MAX_WORDS budget (300 words)
   - Applied to paragraph, table, and figure chunks

2. **Retrieval** (`retrieve.py`):
   - Breadcrumbs are part of `chunk.content` and `enriched_content`
   - Included in vector embeddings (semantic search)
   - Included in `content_tsvector` (lexical search)
   - Passed to BGE reranker for relevance scoring
   - Current tsvector trigger: `to_tsvector('english', COALESCE(NEW.content, ''))`

3. **Consolidation** (`consolidate_context.py`):
   - Breadcrumbs are **reconstructed** from parent hierarchy via `_get_heading_chain()`
   - Stored separately as `heading_chain` list in `clean_retrieval_context`
   - Original embedded breadcrumbs remain in `content` field

### Database Schema

**Current `chunks` table:**
```sql
- id: INT (PK)
- parent_id: INT (FK to chunks.id, nullable)
- work_id: INT (FK to works.id)
- level: VARCHAR(20) -- H1, H2, H3, H4, H5, H1-chunk, H2-chunk, etc.
- content: TEXT -- Contains "{breadcrumb}\n{actual_content}"
- embedding: VECTOR(768) -- Vectorized content including breadcrumb
- start_line: INT
- end_line: INT
- vector_status: VARCHAR(10) -- no_vec, to_vec, vec, vec_err
- content_tsvector: TSVECTOR -- Full-text search index
```

## Target State

### New Database Schema

**Updated `chunks` table:**
```sql
- id: INT (PK)
- parent_id: INT (FK to chunks.id, nullable)
- work_id: INT (FK to works.id)
- level: VARCHAR(20)
- content: TEXT -- Pure content WITHOUT breadcrumb prefix
- heading_breadcrumbs: TEXT -- Breadcrumb string: "H1 > H2 > H3" or NULL
- embedding: VECTOR(768) -- Vectorized content WITHOUT breadcrumb
- start_line: INT
- end_line: INT
- vector_status: VARCHAR(10)
- content_tsvector: TSVECTOR -- Index on content only (without breadcrumb)
```

### Design Decisions

**Q: Should `heading_breadcrumbs` be TEXT or JSONB array?**
- **Decision: TEXT** (formatted as "H1 > H2 > H3")
- **Rationale:**
  - Matches current format used in chunking
  - Simpler migration (direct string extraction)
  - Easier to display in UI without parsing
  - Can convert to array in application layer if needed
  - Consolidation already produces a list, so we can store either format

**Q: Should embeddings include breadcrumbs?**
- **Decision: NO** (exclude from embeddings)
- **Rationale:**
  - Content itself should be semantically rich enough
  - Breadcrumbs are structural metadata, not semantic content
  - Can add breadcrumbs to reranker input if needed
  - Smaller embedding payload = faster similarity search

**Q: Should `content_tsvector` include breadcrumbs?**
- **Decision: NO** (index content only)
- **Rationale:**
  - Lexical search should focus on actual content
  - Breadcrumbs are redundant (headings already in parent chunks)
  - Can create separate tsvector for breadcrumbs if needed later
  - Cleaner separation of concerns

---

## Implementation Plan

### Phase 1: Database Schema & Migration

#### **Ticket 1.1: Update Chunk Model**
**File:** `src/psychrag/data/models/chunk.py`

**Tasks:**
1. Add new column to Chunk model:
   ```python
   heading_breadcrumbs: Mapped[Optional[str]] = mapped_column(
       String(500),  # Max length for long breadcrumb chains
       nullable=True
   )
   ```
2. Update model docstring to document new field
3. Ensure no breaking changes to relationships

**Acceptance Criteria:**
- Model has new `heading_breadcrumbs` field
- Field is nullable (supports existing data)
- Model tests pass (if any exist)

**Dependencies:** None

---

#### **Ticket 1.2: Create Migration Script 010**
**File:** `migrations/010_refactor_heading_breadcrumbs.py`

**Tasks:**
1. Create Python migration file (not SQL, due to complex data transformation)
2. Implement `upgrade()` function:

   **Step 1: Add new column**
   ```sql
   ALTER TABLE chunks ADD COLUMN heading_breadcrumbs VARCHAR(500) NULL;
   ```

   **Step 2: For each chunk with vector_status = 'vec':**
   - Extract breadcrumb from first line of `content` if content has multiple lines
   - Store breadcrumb in `heading_breadcrumbs`
   - Remove breadcrumb line from `content` (strip first line + newline)
   - Set `vector_status = 'to_vec'` (trigger re-vectorization)
   - Set `embedding = NULL`
   - Update `content_tsvector = to_tsvector('english', new_content)`

   **Step 3: For chunks with vector_status != 'vec':**
   - Extract breadcrumb if present (same logic)
   - Store in `heading_breadcrumbs`
   - Remove from `content`
   - Leave `vector_status` unchanged
   - Update `content_tsvector`

   **Step 4: Verify migration**
   - Log total chunks processed
   - Log chunks with breadcrumbs extracted
   - Log chunks re-vectorized

3. Implement `downgrade()` function:
   - Re-embed breadcrumbs into content
   - Drop `heading_breadcrumbs` column
   - Reset affected chunks to `to_vec`

**Breadcrumb Extraction Logic:**
```python
def extract_breadcrumb(content: str) -> tuple[str | None, str]:
    """
    Extract breadcrumb from content if present.

    Based on database verification, the first line is ALWAYS the breadcrumb
    if the content has multiple lines. Single-line content has no breadcrumb.

    Returns:
        (breadcrumb, clean_content) tuple
    """
    if not content:
        return None, content

    # If content has multiple lines, first line is the breadcrumb
    if '\n' in content:
        lines = content.split('\n', 1)
        breadcrumb = lines[0].strip()
        # Get remaining content (after first line and newline)
        clean_content = lines[1] if len(lines) > 1 else ''
        return breadcrumb, clean_content

    # Single-line content has no breadcrumb
    return None, content
```

**Batch Processing:**
- Process in batches of 1000 chunks to avoid memory issues
- Commit after each batch
- Log progress

**Acceptance Criteria:**
- Migration script runs without errors
- All chunks with breadcrumbs have them extracted to new column
- Content no longer contains embedded breadcrumbs
- Chunks with `vec` status are reset to `to_vec` with NULL embeddings
- `content_tsvector` is updated for all affected chunks
- Migration is reversible via `downgrade()`

**Dependencies:** Ticket 1.1

**Estimated Complexity:** High (data migration with validation)

---

#### **Ticket 1.3: Verify content_tsvector Trigger**
**File:** Check existing trigger, document findings

**Tasks:**
1. Connect to database and inspect current trigger:
   ```sql
   SELECT pg_get_triggerdef(oid)
   FROM pg_trigger
   WHERE tgname = 'tsvector_update';
   ```

2. Verify trigger function matches `retrieve.py` lexical search:
   - Current trigger: `to_tsvector('english', COALESCE(NEW.content, ''))`
   - Lexical search: Uses `websearch_to_tsquery('english', :query)`
   - **Conclusion:** Trigger is correct and does NOT need modification

3. Document that trigger automatically updates tsvector when content changes

**Acceptance Criteria:**
- Trigger function verified and documented
- Confirmed that migration's manual tsvector updates are necessary (trigger only fires on content UPDATE)

**Dependencies:** None

**Estimated Complexity:** Low (verification only)

---

### Phase 2: Chunking Changes

#### **Ticket 2.1: Update content_chunking.py - Store Breadcrumbs Separately**
**File:** `src/psychrag/chunking/content_chunking.py`

**Tasks:**
1. **Modify `_create_paragraph_chunks()`** (lines 283-465):
   - Change from embedding breadcrumbs in content to returning them separately
   - Update returned chunk dict to include `heading_breadcrumbs` key:
     ```python
     chunks.append({
         'content': chunk_text,  # WITHOUT breadcrumb prefix
         'heading_breadcrumbs': breadcrumb_text,  # Separate field
         'start_line': current_start_line,
         'end_line': current_end_line,
         'heading_line': h_line,
         'level': level,
         'vector_status': 'to_vec'
     })
     ```

2. **Update word count logic** (lines 333-336):
   - Remove breadcrumb word deduction from `available_words`
   - Breadcrumbs no longer count against MAX_WORDS budget

3. **Modify `_create_table_chunks()`** (lines 468-491):
   - Same changes as paragraph chunks

4. **Modify `_create_figure_chunks()`** (lines 494-517):
   - Same changes as paragraph chunks

5. **Update `chunk_content()` save logic** (lines 760-776):
   - Add `heading_breadcrumbs` when creating Chunk objects:
     ```python
     chunk = Chunk(
         parent_id=parent_id,
         work_id=work_id,
         level=level_str,
         content=chunk_data['content'],  # No breadcrumb
         heading_breadcrumbs=chunk_data.get('heading_breadcrumbs'),
         embedding=None,
         start_line=chunk_data['start_line'],
         end_line=chunk_data['end_line'],
         vector_status=chunk_data['vector_status']
     )
     ```

**Acceptance Criteria:**
- Chunks created with breadcrumbs in separate column
- Content no longer contains embedded breadcrumbs
- Breadcrumbs still capture full heading hierarchy
- Word count logic updated (breadcrumbs don't count against MAX_WORDS)
- All chunk types (paragraph, table, figure) updated consistently

**Dependencies:** Ticket 1.1, Ticket 1.2

**Estimated Complexity:** Medium

---

#### **Ticket 2.2: Test Chunking Changes**
**File:** Create/update tests for content_chunking

**Tasks:**
1. Create test fixtures with sample markdown containing headings
2. Test that breadcrumbs are extracted correctly
3. Test that content does not contain breadcrumbs
4. Test that `heading_breadcrumbs` field is populated
5. Verify edge cases:
   - Chunks with no parent heading (NULL breadcrumbs)
   - Deeply nested headings (H1 > H2 > H3 > H4 > H5)
   - Chunks with very long breadcrumbs

**Acceptance Criteria:**
- Unit tests pass for all chunk types
- Edge cases handled correctly
- Test coverage for breadcrumb extraction

**Dependencies:** Ticket 2.1

**Estimated Complexity:** Medium

---

### Phase 3: Retrieval Changes

#### **Ticket 3.1: Update retrieve.py - Handle Breadcrumbs from New Column**
**File:** `src/psychrag/retrieval/retrieve.py`

**Tasks:**
1. **Analyze impact:**
   - Dense search: Uses `chunk.embedding` (already excludes breadcrumbs after migration)
   - Lexical search: Uses `content_tsvector` (already excludes breadcrumbs after migration)
   - Content enrichment: Uses `chunk.content` (already clean after migration)
   - Reranking: Currently uses `chunk.enriched_content` - **may need breadcrumbs added back**

2. **Decision: Should reranker see breadcrumbs?**
   - **Option A:** Add breadcrumbs to enriched_content for reranking
     - Pro: Provides hierarchical context to reranker
     - Con: Changes reranking behavior

   - **Option B:** Keep breadcrumbs separate, reranker sees content only
     - Pro: Simpler, no behavioral changes
     - Con: Loses some context

   - **Recommendation:** Start with Option B (no changes), add Option A if reranking quality degrades. That's right, keep Option A -- I confirm.

3. **Option A chosen:**
   - Modify enriched content creation (line 713):
     ```python
     # Enrich content
     enriched = _enrich_content(chunk, work) if work else chunk.content

     # Prepend breadcrumbs for reranker context
     if chunk.heading_breadcrumbs:
         enriched = f"{chunk.heading_breadcrumbs}\n{enriched}"
     ```

4. **Update saved context** (lines 759-774):
   - Add `heading_breadcrumbs` to saved context:
     ```python
     context_data.append({
         "id": chunk.id,
         "parent_id": chunk.parent_id,
         "work_id": chunk.work_id,
         "content": chunk.content,
         "heading_breadcrumbs": chunk.heading_breadcrumbs,  # NEW
         "enriched_content": chunk.enriched_content,
         "start_line": chunk.start_line,
         "end_line": chunk.end_line,
         "level": chunk.level,
         "rrf_score": chunk.rrf_score,
         "rerank_score": chunk.rerank_score,
         "entity_boost": chunk.entity_boost,
         "final_score": chunk.final_score
     })
     ```

**Acceptance Criteria:**
- Retrieval works with new schema
- Breadcrumbs available in retrieved_context
- Decision documented on reranker breadcrumb inclusion
- No degradation in retrieval quality (verify with test queries)

**Dependencies:** Ticket 1.2, Ticket 2.1

**Estimated Complexity:** Low-Medium

---

#### **Ticket 3.2: Test Retrieval Changes**
**File:** Create/update tests for retrieve.py

**Tasks:**
1. Test retrieval with new schema
2. Verify breadcrumbs appear in `retrieved_context`
3. Test that embeddings work correctly (without embedded breadcrumbs)
4. Test lexical search works correctly (without embedded breadcrumbs)
5. Compare retrieval quality before/after (manual testing)

**Acceptance Criteria:**
- Retrieval tests pass
- Breadcrumbs accessible from retrieved results
- Quality verification complete

**Dependencies:** Ticket 3.1

**Estimated Complexity:** Medium

---

### Phase 4: Consolidation Changes

#### **Ticket 4.1: Update consolidate_context.py - Use New Column**
**File:** `src/psychrag/augmentation/consolidate_context.py`

**Tasks:**
1. **Understand current behavior:**
   - Currently calls `_get_heading_chain()` to reconstruct breadcrumbs from parent hierarchy
   - Stores reconstructed breadcrumbs as `heading_chain` list
   - Original embedded breadcrumbs remain in content

2. **Update to use new column:**

   **Option A: Use chunk.heading_breadcrumbs directly**
   - Simpler approach
   - Trusts chunking-time breadcrumbs
   - May not account for consolidation (parent replacement)

   **Option B: Continue reconstructing from parents**
   - Handles consolidation better (chunks may have moved up hierarchy)
   - More accurate for replaced/merged chunks
   - Current behavior, proven to work

   **Recommendation:** **Option B** - Continue using `_get_heading_chain()` but format as string instead of list
   I confirm we should use Option B

3. **Modify `_get_heading_chain()`** (lines 59-98):
   - Option 1: Return string instead of list:
     ```python
     return ' > '.join(chain)  # String: "H1 > H2 > H3"
     ```

   - Option 2: Keep returning list, convert to string when saving:
     ```python
     # In save logic (line 409):
     'heading_chain': ' > '.join(group.heading_chain) if group.heading_chain else None
     ```

   **Recommendation:** Option 2 (keep list for flexibility)
   I confirm Option 2

4. **Update data saving** (lines 399-410):
   - Store breadcrumbs as string in `clean_retrieval_context`:
     ```python
     context_data.append({
         'chunk_ids': group.chunk_ids,
         'parent_id': group.parent_id,
         'work_id': group.work_id,
         'content': group.content,  # Already clean (no embedded breadcrumbs)
         'start_line': group.start_line,
         'end_line': group.end_line,
         'score': group.score,
         'heading_chain': ' > '.join(group.heading_chain) if group.heading_chain else None
     })
     ```

5. **Verify `_finalize_group()`** (lines 165-200):
   - Check if it tries to extract breadcrumbs from content (lines 184-190)
   - **Issue:** This code expects breadcrumbs in content!
     ```python
     # Get first line (heading) from first item
     first_item = items[0]
     if 'content' in first_item:
         first_line = first_item['content'].split('\n')[0]
         # Only prepend if content doesn't already start with this heading
         if not content.startswith(first_line):
             content = first_line + '\\n\\n' + content
     ```
   - **Fix:** This is checking for heading (like "## Introduction"), not breadcrumb
   - Verify this logic still works with clean content

**Acceptance Criteria:**
- Consolidation uses new breadcrumb column
- Breadcrumbs correctly reflect consolidated hierarchy
- `clean_retrieval_context` contains breadcrumbs as string
- Content remains clean (no embedded breadcrumbs)
- Merging/replacing logic works correctly

**Dependencies:** Ticket 3.1

**Estimated Complexity:** Medium

---

#### **Ticket 4.2: Test Consolidation Changes**
**File:** Create/update tests for consolidate_context.py

**Tasks:**
1. Test consolidation with new schema
2. Verify breadcrumbs are correct after merging
3. Verify breadcrumbs are correct after parent replacement
4. Test edge cases:
   - Chunks with no breadcrumbs
   - Multiple consolidation levels
   - Cross-work consolidation (if applicable)

**Acceptance Criteria:**
- Consolidation tests pass
- Breadcrumbs accurate in consolidated groups
- Edge cases handled

**Dependencies:** Ticket 4.1

**Estimated Complexity:** Medium

---

### Phase 5: Integration & Validation

#### **Ticket 5.1: End-to-End Testing**
**File:** Integration tests or manual testing script

**Tasks:**
1. **Full pipeline test:**
   - Start with raw markdown document
   - Run chunking → verify breadcrumbs in DB
   - Run vectorization → verify embeddings exist
   - Run retrieval → verify breadcrumbs in retrieved_context
   - Run consolidation → verify breadcrumbs in clean_retrieval_context

2. **Regression testing:**
   - Compare retrieval results before/after migration
   - Verify no degradation in recall/precision
   - Check that breadcrumbs are accessible and correct

3. **Performance testing:**
   - Verify query performance hasn't degraded
   - Check indexing performance

**Acceptance Criteria:**
- End-to-end pipeline works correctly
- No regressions in retrieval quality
- Performance acceptable

**Dependencies:** All previous tickets

**Estimated Complexity:** High

---

#### **Ticket 5.2: Documentation & Cleanup**
**File:** Update documentation

**Tasks:**
1. Update module docstrings to reflect new breadcrumb handling
2. Update database schema documentation
3. Document migration process in README or docs
4. Add inline comments for complex breadcrumb logic
5. Update any API documentation (if applicable)
6. Archive this plan document with completion notes

**Acceptance Criteria:**
- All relevant documentation updated
- Schema changes documented
- Migration process documented

**Dependencies:** Ticket 5.1

**Estimated Complexity:** Low

---

## Migration Execution Plan

### Pre-Migration Checklist
- [ ] Backup database
- [ ] Verify all previous migrations applied
- [ ] Note current chunk count and vec status distribution
- [ ] Test migration on staging/dev database first

### Migration Steps
1. **Run Migration 010:**
   ```bash
   venv\Scripts\python -m psychrag.data.run_migrations
   ```

2. **Verify Migration:**
   ```sql
   -- Check new column exists
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'chunks' AND column_name = 'heading_breadcrumbs';

   -- Check breadcrumb extraction worked
   SELECT
       COUNT(*) as total_chunks,
       COUNT(heading_breadcrumbs) as chunks_with_breadcrumbs,
       SUM(CASE WHEN vector_status = 'to_vec' THEN 1 ELSE 0 END) as to_vec_count
   FROM chunks;

   -- Sample extracted breadcrumbs
   SELECT id, heading_breadcrumbs, LEFT(content, 100) as content_preview
   FROM chunks
   WHERE heading_breadcrumbs IS NOT NULL
   LIMIT 10;
   ```

3. **Re-vectorize Chunks:**
   - Run vectorization script on all `to_vec` chunks
   - Monitor progress and errors

4. **Verify Results:**
   - Run test queries
   - Compare results with pre-migration baseline
   - Check breadcrumb accessibility in UI/API

### Rollback Plan
If migration fails or causes issues:
```bash
# Run downgrade (if implemented)
venv\Scripts\python -m psychrag.data.rollback_migration --to 009

# Restore from backup
# [Database-specific restore commands]
```

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Migration fails mid-execution | High | Low | Batch processing, transaction safety, backup |
| Breadcrumb extraction fails | Medium | Medium | Extensive testing, validation queries |
| Re-vectorization takes too long | Low | High | Run in background, monitor progress |
| Retrieval quality degrades | High | Low | A/B testing, rollback capability |
| UI breaks due to schema change | Medium | Medium | Update UI in same release, test thoroughly |
| Content_tsvector not updated | Medium | Low | Manual update in migration, trigger verification |

---

## Success Criteria

- [ ] All chunks have breadcrumbs extracted to new column
- [ ] No chunks have embedded breadcrumbs in content
- [ ] All affected chunks successfully re-vectorized
- [ ] Retrieval returns correct results with breadcrumbs
- [ ] Consolidation produces correct breadcrumbs
- [ ] No performance degradation
- [ ] All tests passing
- [ ] Documentation updated

---

## Ticket Summary

| Phase | Ticket | Complexity | Dependencies |
|-------|--------|-----------|--------------|
| **Phase 1** | 1.1 Update Chunk Model | Low | None |
| | 1.2 Create Migration 010 | High | 1.1 |
| | 1.3 Verify tsvector Trigger | Low | None |
| **Phase 2** | 2.1 Update content_chunking.py | Medium | 1.1, 1.2 |
| | 2.2 Test Chunking | Medium | 2.1 |
| **Phase 3** | 3.1 Update retrieve.py | Low-Med | 1.2, 2.1 |
| | 3.2 Test Retrieval | Medium | 3.1 |
| **Phase 4** | 4.1 Update consolidate_context.py | Medium | 3.1 |
| | 4.2 Test Consolidation | Medium | 4.1 |
| **Phase 5** | 5.1 End-to-End Testing | High | All previous |
| | 5.2 Documentation | Low | 5.1 |

**Total Tickets:** 10
**Estimated Duration:** 3-5 days (with testing)
**Critical Path:** 1.1 → 1.2 → 2.1 → 3.1 → 4.1 → 5.1

---

## Notes

- **Breadcrumbs as TEXT vs JSONB:** We chose TEXT for simplicity and compatibility with current format
- **Embeddings:** Will NOT include breadcrumbs (cleaner semantic representation)
- **Lexical Search:** Will NOT index breadcrumbs (focus on content)
- **Reranker:** Decision point - may add breadcrumbs back for context (Ticket 3.1)
- **Migration is Python:** Due to complex string extraction and batch processing
- **Re-vectorization Required:** All existing `vec` chunks must be re-vectorized
