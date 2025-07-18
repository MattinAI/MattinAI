#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER langflow WITH PASSWORD 'langflow';
    CREATE DATABASE langflow;
    GRANT ALL PRIVILEGES ON DATABASE langflow TO langflow;
	GRANT ALL PRIVILEGES ON DATABASE langflow TO postgres;
	GRANT ALL ON SCHEMA public TO postgres;
    GRANT ALL ON SCHEMA public TO langflow;

	-- Connect to the langflow database
	\c langflow
    GRANT ALL ON SCHEMA public TO langflow;
    GRANT ALL ON SCHEMA public TO postgres;
EOSQL