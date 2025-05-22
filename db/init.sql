CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(50),
    title VARCHAR(255),
    summary TEXT,
    contact_info JSONB,
    skills TEXT[],
    experience JSONB,
    education JSONB,
    languages TEXT[],
    certifications TEXT[],
    hobbies TEXT[],
    portfolio JSONB,
    CONSTRAINT unique_name UNIQUE (name)
);
