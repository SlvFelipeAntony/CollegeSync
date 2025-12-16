CREATE SCHEMA IF NOT EXISTS collegesync AUTHORIZATION postgres;

-- ============================================================
--  TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS collegesync.users (
	id BIGSERIAL PRIMARY KEY,
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(150) NOT NULL,
	email VARCHAR(256) UNIQUE NOT NULL,
	birth_date DATE,
	hash_password VARCHAR(256) NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', NOW()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', NOW())
);

CREATE TABLE IF NOT EXISTS collegesync.students (
	id BIGSERIAL PRIMARY KEY,
	user_id BIGINT UNIQUE NOT NULL,
	FOREIGN KEY (user_id)
		REFERENCES collegesync.users
		ON DELETE CASCADE
		ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS collegesync.teachers (
	id BIGSERIAL PRIMARY KEY,
	user_id BIGINT UNIQUE NOT NULL,
	FOREIGN KEY (user_id)
		REFERENCES collegesync.users
		ON DELETE CASCADE
		ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS collegesync.appointments (
	id BIGSERIAL PRIMARY KEY,
	
	scheduled_at TIMESTAMPTZ NOT NULL,
	notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', NOW()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', NOW())
)
