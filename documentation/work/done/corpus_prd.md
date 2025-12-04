# Corpus page PRD

Build a page similar to `@psychrag_ui\src\app\sanitization\page.tsx` in the following url: `/corpus`:

1. The right nav link should be right at the top
2. Move Init & Status page (@psychrag_ui\src\app\init\page.tsx) into the same page under Settings(@psychrag_ui\src\app\settings\page.tsx) but a new tab (first tab--"Init/Status")
3. The new page we're building (`/corpus`) should be based on the following data:
    * All the works in `works` table in the DB (`/src/psychrag/data/models/work.py`) that have `works.processing_status` as:

    ```json
    {
    "content_chunks": "completed",
    "heading_chunks": "completed"
    }
    ```

4. the new page (`/corpus`) should have the following:
    * Overview that has:
        * Total works
        * Chunk counts by vector status (count chunks for each status separately):
            * "no_vec" - chunks not queued for vectorization
            * "to_vec" - chunks queued for vectorization
            * "vec" - chunks successfully vectorized
            * "vec_err" - chunks with vectorization errors
    * Works:
        * Title
        * Authors
        * Path -- the path of `works.files['sanitized']['path']`
    * Each of the rows in the above "Works" table should be clickable and it should open `/corpus/{id}`

5. Work Examine page (`/corpus/{id}` -- id = work id):
    * Very similar to `conv/{id}/inspect_original_md` except that it should open the "sanitized" version (`works.files['sanitized']['path']`) and it should be "read-only" -- ensure you use `import { MarkdownEditor } from "@/components/markdown-editor";`
    * For this new page and `conv/{id}/inspect_original_md` fix so there isn't this annoying double scrollbar between the browser and the rendered/markdown view -- just show the content below the heading and let it scroll in the browser not in a frame underneath

## Note

* Create new route in `/src/psychrag_api/routers/` for `corpus`
* If needed create a module in a new folder in `/src/psychrag/` called `works`

Note: **Ask any questions if unclear**