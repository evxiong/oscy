-- oscy database schema
CREATE TYPE award_type AS ENUM('oscar', 'emmy');

CREATE TYPE entity_type AS ENUM('person', 'company', 'country', 'network');

CREATE
OR REPLACE FUNCTION integer_to_ordinal (num integer) RETURNS text AS $$
    SELECT 
        num::text ||
        CASE
            WHEN num % 100 IN (11,12,13) THEN 'th'
            WHEN num % 10 = 1 THEN 'st'
            WHEN num % 10 = 2 THEN 'nd'
            WHEN num % 10 = 3 THEN 'rd'
            ELSE 'th'
        END;
$$ LANGUAGE SQL;

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS
    editions (
        id serial PRIMARY KEY,
        award award_type NOT NULL, -- 'oscar' or 'emmy'
        iteration integer NOT NULL,
        official_year varchar(10) NOT NULL, -- listed year, ex. '1927/28'
        ceremony_date date NOT NULL
    );

CREATE TABLE IF NOT EXISTS
    category_groups (
        id serial PRIMARY KEY,
        award award_type NOT NULL,
        name text NOT NULL -- ex. 'Acting'
    );

CREATE TABLE IF NOT EXISTS
    categories (
        id serial PRIMARY KEY,
        award award_type NOT NULL,
        name text NOT NULL, -- category nickname, ex. 'Animated Feature'
        category_group_id integer REFERENCES category_groups (id) ON DELETE SET NULL
    );

CREATE TABLE IF NOT EXISTS
    category_names (
        id serial PRIMARY KEY,
        award award_type NOT NULL,
        official_name text NOT NULL, -- specific category name according to official source, ex. 'ANIMATED FEATURE FILM'
        common_name text NOT NULL, -- common category name, ex. 'Best Animated Feature Film'
        category_id integer NOT NULL REFERENCES categories (id)
    );

CREATE TABLE IF NOT EXISTS
    editions_category_names (
        id serial PRIMARY KEY,
        edition_id integer NOT NULL REFERENCES editions (id),
        category_name_id integer NOT NULL REFERENCES category_names (id)
    );

CREATE TABLE IF NOT EXISTS
    entities (
        id serial PRIMARY KEY,
        imdb_id text UNIQUE NOT NULL,
        type entity_type NOT NULL,
        name text NOT NULL
    );

CREATE TABLE IF NOT EXISTS
    titles (
        id serial PRIMARY KEY,
        imdb_id text UNIQUE NOT NULL,
        award award_type NOT NULL,
        title text NOT NULL -- name of film or show
    );

CREATE TABLE IF NOT EXISTS
    nominees (
        id serial PRIMARY KEY,
        award award_type NOT NULL,
        edition_id integer NOT NULL REFERENCES editions (id),
        category_name_id integer NOT NULL REFERENCES category_names (id),
        statement text NOT NULL,
        is_person boolean NOT NULL, -- whether the nominee is primarily a person (T) or a title (F)
        pending boolean NOT NULL DEFAULT FALSE, -- whether ceremony results are pending
        winner boolean NOT NULL, -- whether any title in this nominee won
        note text NOT NULL,
        official boolean NOT NULL, -- whether this nominee is considered official (for Oscars)
        stat boolean NOT NULL -- whether this nominee counts towards aggregated nomination stats
    );

CREATE TABLE IF NOT EXISTS
    nominees_titles (
        id serial PRIMARY KEY,
        nominee_id integer NOT NULL REFERENCES nominees (id),
        title_id integer NOT NULL REFERENCES titles (id),
        detail text[] NOT NULL, -- characters, song titles, or dance numbers assoc. with this title
        winner boolean NOT NULL, -- whether this particular title won (only important for 3rd oscars)
        UNIQUE (nominee_id, title_id)
    );

CREATE TABLE IF NOT EXISTS
    nominees_entities (
        id serial PRIMARY KEY,
        nominee_id integer NOT NULL REFERENCES nominees (id),
        entity_id integer NOT NULL REFERENCES entities (id),
        name text NOT NULL, -- name listed on this nomination (could be alias)
        statement_ind integer NOT NULL, -- start index of name in nomination statement
        role text NOT NULL, -- entity's role on set (if applicable)
        UNIQUE (nominee_id, entity_id)
    );

CREATE INDEX title_trgm_idx ON titles USING GIST (title gist_trgm_ops);

CREATE INDEX entity_trgm_idx ON entities USING GIST (name gist_trgm_ops);