-- Migration 012: Create prompt_meta table for prompt template metadata
-- This table stores metadata about prompt template variables (one record per function_tag)

CREATE TABLE IF NOT EXISTS prompt_meta (
    id SERIAL PRIMARY KEY,
    function_tag VARCHAR(100) UNIQUE NOT NULL,
    variables JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on function_tag for efficient lookups
CREATE INDEX IF NOT EXISTS idx_prompt_meta_function_tag ON prompt_meta(function_tag);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_prompt_meta_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_prompt_meta_updated_at
    BEFORE UPDATE ON prompt_meta
    FOR EACH ROW
    EXECUTE FUNCTION update_prompt_meta_updated_at();

-- Add comment to the table
COMMENT ON TABLE prompt_meta IS 'Metadata for prompt templates including variable descriptions';
COMMENT ON COLUMN prompt_meta.function_tag IS 'Unique identifier for the prompt function (links to prompt_templates.function_tag)';
COMMENT ON COLUMN prompt_meta.variables IS 'JSONB array of objects with variable_name and variable_description fields';
