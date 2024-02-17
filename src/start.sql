CREATE TABLE IF NOT EXISTS users(
    username TEXT UNIQUE,
    password TEXT,
    salt TEXT,
    session TEXT,
    roles RolesEnum
);
CREATE TABLE IF NOT EXISTS folders(
    name TEXT,
    accessers TEXT ARRAY,
    id TEXT
);
CREATE TABLE IF NOT EXISTS files(
    folder TEXT,
    id TEXT,
    last_updated TIMESTAMP,
    path TEXT
)