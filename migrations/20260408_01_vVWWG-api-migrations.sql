-- api migrations
-- depends: 20260324_01_pUn2z

CREATE SCHEMA "base";

CREATE TABLE "base"."user" (
    id SERIAL,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    inserted_at TIMESTAMP NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP,

    CONSTRAINT user_pk PRIMARY KEY (id)
);

CREATE TABLE "base"."refresh" (
    id SERIAL,
    user_id INTEGER NOT NULL,
    token UUID NOT NULL UNIQUE,
    used BOOLEAN DEFAULT FALSE,
    inserted_at TIMESTAMP NOT NULL,

    CONSTRAINT refresh_pk PRIMARY KEY (id)
);