-- Enable extensions required for the pharmacovigilance database
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Confirm extensions are loaded
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'pg_trgm');