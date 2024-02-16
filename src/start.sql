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
)