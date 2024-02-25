FROM python:3.11-alpine as base
RUN python3 -m pip install poetry
RUN python3 -m poetry config virtualenvs.in-project true
FROM base as build
WORKDIR /folderistic
COPY . .
RUN apk update 
RUN apk add --no-cache make gcc linux-headers build-base 
RUN python3 -m poetry install
RUN apk del gcc linux-headers build-base
FROM python:3.11-alpine as run
WORKDIR /folderistic
COPY --from=build /folderistic .
CMD ["poetry", "run", "uvicorn", "src:app"]