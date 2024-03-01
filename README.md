# Folderistic

Partly Google Drive Clone with Login/File uploading/Role management system

## What does this project solves?

This project is requested by my mother with problem having no where official to upload school files in with her teachers. She wanted to use Google Drive but it doesn't have role where you can just upload file but can't delete it and have full logs of what's going on. So this project is trying to solve her problems.

## Requirements

- Python 3.11
- Poetry
- ASGI Servers (uvicorn is default)
- PostgreSQL 14 (please raise your connection limit to something like 200)

## Metrics

Metrics will be opened at both `/metrics` and `/metrics-starlette`

## Setup

create `.env`

```sh
FOLDERISTIC_HOST=postgres db host
FOLDERISTIC_USER=postgres db user
FOLDERISTIC_PASS=postgres db user password
FOLDERISTIC_DB=postgres db name
```

and execute code in `src/types.sql` then you are ready to go
just start up with `poetry install` and then run it by `poetry run uvicorn src:app`

### Docker (Compose)

```yaml
services:
    folderistic:
        image: ghcr.io/timelessnesses/folderistic:latest
        environment:
            - FOLDERISTIC_HOST=db
            - FOLDERISTIC_USER=folderistic
            - FOLDERISTIC_PASS=folderistic
            - FOLDERISTIC_DB=folderistic
    db:
        image: postgres:14
        environment:
            - POSTGRES_USER=folderistic
            - POSTGRES_PASSWORD=folderistic
            - POSTGRES_DB=folderistic
        volumes:
            - data:/var/lib/postgresql/data
volumes:
    data:
```
Copy Paste this code to a file named `compose.yaml` in a folder then run `docker compose run` to run the application
