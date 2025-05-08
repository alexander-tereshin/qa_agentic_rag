CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    gender TEXT,
    title TEXT,
    summary TEXT,
    contact_info JSONB,
    skills TEXT[],
    experience JSONB,
    education JSONB,
    languages TEXT[],
    certifications TEXT[],
    hobbies TEXT[],
    portfolio JSONB
);
