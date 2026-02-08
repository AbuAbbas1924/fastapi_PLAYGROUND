#!/bin/bash

postgres(){
    docker run --name postgres \
        -e POSTGRES_USER=root \
        -e POSTGRES_PASSWORD=root \
        -e POSTGRES_DB=fastapi-playground \
        -p 5432:5432 \
        -d postgres:18.1-alpine
}

app_build(){
    docker build -t fastapi-playground-image .
}

app_run(){
    docker run --rm --name fastapi-playground \
    --link postgres:postgres \
    -e DATABASE_URL="postgresql+asyncpg://root:root@postgres:5432/fastapi-playground" \
    -p 8000:8000 \
    -v $PWD:/app \
    fastapi-playground-image
}

$1