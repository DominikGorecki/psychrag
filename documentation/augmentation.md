# Augmentation

This step does the following:
* Takes the raw results in the `Query` object that is saved in `retrieval_context` and consolidates them into a cleaner object to send to the LLM as context. We'll call this the `clean_retrieval_context`.
* It converts the `clean_retrieval_context` JSON into md format that will be easy for the LLM to use. 
* It provides the instructions how to use the clean retrieval context markdown
* It then provides the original query

# Consolidation -- Generating a Clean Retrieval Context

1. Group all items by `work id` and `parent_id`
2. Based on `start_line` and `end_line` of the chunks and the `start_line` and `end_line` of the parent:
    * If the chunks of the parent cover 50% or more of the parent, replace all the chunks with the parent. Use the highest `final_score` of the group as the as the `score`. This will be the entry for this group.
    * If the chunks of the parent cover less than 50% of the parent, then try to combine the chunks if they are within each other based on the `start_line` and `end_line`:
        1. Order by `start_line`
        2. If any chunk i `end_line` of one chunk is within 7 lines of the `start_line` of the next chunk, then group them together based on the line:

            * `start_line`: based on the first chunk in the group
            * `end_line`: based on the last chunk in the group
            * `content`: read from the original `<work>.sanitized.md` file found in `works` (matched on `work_id`) in the `markdown_path` column. Use the `start_line` and `end-line` determined in the two points above
            * `score`: highest `final_score` of the group
            * Append the title of the first chunk in the group -- the first line of the first chunk should be copied over to the top of the `content` with a line space in between
            * `parent_id`: stays the same--should be the same for the whole group

    * When there are nested parents, follow the above steps but from lowest level to the top. That is, first determine the grouping based on the lower level parents and then work up to higher level parents. 
    * The final `clean_retrieval_context` should have the following properties:
        * `chunk_ids: [chunk_id]`: array of the chunk ids in the group (could be just 1)
        * `parent_id`: Since we're grouping by parent, the parent id of the group
        * `work_id`: all need to be in the same work
        * `content`: Content generated as explained above
        * `start_line` and `end_line`: as explained above
        * `score`: highest `final_score` of the group




3. 