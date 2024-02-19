# Folderistic

create `.env`

```sh
FOLDERISTIC_HOST=postgres db host
FOLDERISTIC_USER=postgres db user
FOLDERISTIC_PASS=postgres db user password
FOLDERISTIC_DB=postgres db name
```

and execute code in `src/types.sql` then you are ready to go
just start up with `poetry install` and then run it by `poetry run uvicorn --reload src:app`
