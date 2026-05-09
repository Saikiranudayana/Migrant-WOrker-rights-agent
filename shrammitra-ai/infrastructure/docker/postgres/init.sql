-- PostgreSQL initialization script
-- Runs once when the postgres container is first created.

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- for fast LIKE/ILIKE on text columns

-- Create the application user with limited privileges
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'shrammitra') THEN
        CREATE ROLE shrammitra WITH LOGIN PASSWORD 'changeme_in_production';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE shrammitra_db TO shrammitra;
GRANT USAGE ON SCHEMA public TO shrammitra;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO shrammitra;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO shrammitra;

-- All tables are created by SQLAlchemy at startup via create_all().
-- This file only sets up the database-level prerequisites.

\echo 'ShramMitra database initialized successfully.'
