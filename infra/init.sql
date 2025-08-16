-- Initialize Curestry database
-- This file is executed when PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Basic database initialization
\echo 'Database initialized successfully';