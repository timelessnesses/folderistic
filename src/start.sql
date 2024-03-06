CREATE TABLE IF NOT EXISTS users(
    username TEXT UNIQUE,
    password TEXT,
    salt TEXT,
    session TEXT,
    roles RolesEnum,
    first_connected TIMESTAMP WITH TIME ZONE,
    last_connected TIMESTAMP WITH TIME ZONE
);
CREATE TABLE IF NOT EXISTS folders(
    name TEXT,
    accessers TEXT ARRAY,
    id TEXT
);
CREATE TABLE IF NOT EXISTS files(
    folder TEXT,
    id TEXT,
    last_updated TIMESTAMP WITH TIME ZONE,
    path TEXT,
    name TEXT,
    who TEXT
)