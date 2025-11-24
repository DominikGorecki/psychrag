## Retrieval: Dense + Lexical + RRF

Goal:

Pull a candidate pool of chunks by combining:
* Dense retrieval (vector similarity)
* Lexical retrieval (BM25)

Then fuse rankings via Reciprocal Rank Fusion (RRF)

### Python Dense + Lexical Retrieval 

* Run in separate queries and the fuse scores in python

Uses postgresSQL way of performing dense retrieval per query;
for each embedding query (Q_orig, Q_MQE_1, Q_MQE_2, Q_MQE_3, ..., Q_HyDE):
* Dense: pgvector column `embedding` with `hnsw` and embedding <-> query_vector for each query. Limit each query results to top 15 by default (can be set).
    * Dense: SELECT ... ORDER BY embedding <-> :vec LIMIT 15

For each embedding query (Q_orig, Q_MQE_1, Q_MQE_2, Q_MQE_3, ...):
* Lexical: using postgress full-text search (tsvector + ts_rang) for each query. Limit each query results to top 10 by default (can be set).
    * Lexical: SELECT ... ORDER BY ts_rank(...) DESC LIMIT 10

### Python for RRF (Reciprocal Rank Fusion)

* Combines the results from Dense and Lexical retrieval into one set. Whole set will include:
    * Dense results: 15 (default top dense) * 5 (1 orig, 1 HyDe, 3 default MQE) => 75 total
    * Lexical results: 10 (default top lex) * 4 (1 orig, 3 default MQE) => 40 total
    * If defaults are used we should have a total of **115 results** in our combined set

* Use Reciprocal Rank Fusion to compare all results against one another and pick top `K` items (default: `K = 60`):

[
\text{RRFscore}(d) = \sum_{L} \frac{1}{K + r_L(d)}
]

Now we have:

* Fused **all dense + lexical + all queries** into a single ranking.
* **top K (60 default)** candidate `chunk_id`s.

### BGE-reranker & Intent/entity bias

Now you need the **full chunk text** and metadata: 

* id 
* parent_id
* work_id
* content
* start_line
* end_line

Enrich each `Candidate` by using this algorithm:

* Any `Candidate` chunk with more than 350 characters, leave as is 
* Any `Candidate` chunk with less then 350 characters:
    * Copy over 5 sentences above `start_line` from the original `work` (based on `workd_id`) and the `markdown_path`
    * Append the these lines above the `content` of the candidate 
    * Copy over 5 sentences below `end_line` in the original `work` and append them after the content
    * In both cases, leave one blank line in the append
    * In both cases, only do it in memory and do not affect the DB 

* Use `BAAI/bge-reranker-large" from hugging face with the following default settings:
    * `torch_dtype=torch.float16` on GPU saves memory and is fine on a 1080.
    * `batch_size=8` is a safe starting point; if you OOM, drop to 4 or 2.
    * `max_length=512` is plenty for your chunks; shorter (e.g., 384) will reduce VRAM usage further.
    * `truncation=True` to handle cutting

* Only use the **original user question** for re-ranking -- not the expanded queries.

Now we bias our re-ranking based on intent and entities:

* **Entities**: Default entity boost per match -- 0.05
    * Compare normalized text of entity to normalized text on content
    * For any match, boost thee `re-rank` score by 0.05 (unless something different set)
* **Intent**: For now create a method that doesn't do anything--we'll think about an algorithm in the future for this bias--it should be run on each chunk

### Final Sort and Selection
* Based on re-rank score biased for intent & entities, pick the Top `N` -- the default will be 12 (`N = 12`)
* Save these results in the `Queries` table in a `retrieved_context` JSON object (all the 12 chunks with adjusted text, scores, and all the metadata)
