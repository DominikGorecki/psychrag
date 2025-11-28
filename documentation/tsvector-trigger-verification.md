# content_tsvector Trigger Verification

**Date:** 2025-11-27
**Migration:** 004_add_tsvector_and_retrieved_context.sql
**Verification for:** Breadcrumb Refactoring (Migration 010)

## Summary

✅ **The existing `content_tsvector` trigger is CORRECT and does NOT need modification.**

## Trigger Details

### Trigger Function
```sql
CREATE OR REPLACE FUNCTION chunks_content_tsvector_trigger()
RETURNS trigger AS $$
BEGIN
    NEW.content_tsvector := to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Trigger Definition
```sql
CREATE TRIGGER tsvector_update
    BEFORE INSERT OR UPDATE OF content ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION chunks_content_tsvector_trigger();
```

## How It Works

1. **Trigger Type:** `BEFORE INSERT OR UPDATE OF content`
   - Fires automatically when `content` column is modified
   - Runs before the row is written to disk

2. **Vectorization:** `to_tsvector('english', COALESCE(NEW.content, ''))`
   - Converts content to tsvector using English dictionary
   - Handles NULL content gracefully with COALESCE

3. **Automatic Updates:**
   - When content changes, tsvector is automatically updated
   - No manual intervention needed for most operations

## Compatibility with retrieve.py

### Lexical Search Query
From `src/psychrag/retrieval/retrieve.py` (lines 154-160):

```sql
SELECT id
FROM chunks
WHERE content_tsvector @@ websearch_to_tsquery('english', :query)
    AND vector_status = 'vec'
ORDER BY ts_rank_cd(content_tsvector, websearch_to_tsquery('english', :query)) DESC
LIMIT :limit
```

### Analysis
- **Trigger uses:** `to_tsvector('english', ...)`
- **Search uses:** `websearch_to_tsquery('english', :query)`
- **Ranking uses:** `ts_rank_cd(content_tsvector, ...)`

✅ **Perfect compatibility:** Both use the same 'english' dictionary.

## Impact of Breadcrumb Refactoring

### Before Migration 010
- `content` includes embedded breadcrumbs: `"H1 > H2 > H3\nactual content..."`
- `content_tsvector` indexes breadcrumbs + content
- Lexical search matches against both

### After Migration 010
- `content` excludes breadcrumbs: `"actual content..."`
- `content_tsvector` indexes only content (cleaner)
- Lexical search focuses on actual content (better precision)

### Why Manual Update Needed in Migration

The trigger only fires on `INSERT` or `UPDATE OF content`. Migration 010 needs to:

1. **Extract breadcrumbs** from existing content
2. **Update content** to remove breadcrumbs
3. **Manually update tsvector** with clean content

The migration handles this correctly:

```python
connection.execute(
    text("""
        UPDATE chunks
        SET heading_breadcrumbs = :breadcrumb,
            content = :content,
            content_tsvector = to_tsvector('english', :content)
        WHERE id = :id
    """),
    {...}
)
```

When we set `content = :content`, the trigger will fire automatically, but we also explicitly set `content_tsvector` to ensure it uses the clean content immediately.

## Verification Steps

To verify the trigger in a live database:

```sql
-- Check trigger exists
SELECT tgname, tgtype, tgenabled, pg_get_triggerdef(oid)
FROM pg_trigger
WHERE tgrelid = 'chunks'::regclass
  AND tgname = 'tsvector_update';

-- Check trigger function exists
SELECT proname, prosrc
FROM pg_proc
WHERE proname = 'chunks_content_tsvector_trigger';

-- Test trigger on a sample update
BEGIN;
UPDATE chunks
SET content = 'Updated content without breadcrumb'
WHERE id = 1;

-- Verify tsvector was updated
SELECT id, content, content_tsvector
FROM chunks
WHERE id = 1;

ROLLBACK;
```

## Conclusion

**No changes needed to the existing trigger.**

The trigger will continue to work correctly after migration 010:
- It will automatically index new chunks created by `content_chunking.py` (without breadcrumbs)
- It will update tsvector when content is modified
- Migration 010 manually updates tsvector for all existing chunks

**Status:** ✅ VERIFIED - No action required
