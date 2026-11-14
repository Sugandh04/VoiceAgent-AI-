-- VoiceAgent AI — MySQL initialization script
-- Runs once when the MySQL container is first created.

CREATE DATABASE IF NOT EXISTS voiceagent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE voiceagent;

-- SQLAlchemy will create all tables via init_db() on first API startup.
-- This file is kept for any manual seed data or future migrations.

