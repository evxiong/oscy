# Database

This document explains the structure of the oscy database and how to query from
it. The database is contained in [`data/db.dump`](/data/db.dump), which can be
copied by following the instructions in [`data/README.md`](/data/README.md). The
schema file used to create the database is located at
[`backend/db/schema.sql`](/backend/db/schema.sql).

- [Requirements](#requirements)
- [Schema](#schema)
  - [Enums](#enums)
  - [Ceremonies](#ceremonies)
    - [editions](#editions)
  - [Categories](#categories)
    - [category_groups](#category_groups)
    - [categories](#categories-1)
    - [category_names](#category_names)
    - [editions_category_names](#editions_category_names)
  - [Entities & Titles](#entities--titles)
    - [entities](#entities)
    - [titles](#titles)
  - [Nominations](#nominations)
    - [nominees](#nominees)
    - [nominees_titles](#nominees_titles)
    - [nominees_entities](#nominees_entities)
  - [Other tables](#other-tables)
    - [current_versions](#current_versions)
- [Usage](#usage)
  - [How to count nominations and wins](#how-to-count-nominations-and-wins)
    - [Counting nominations](#counting-nominations)
    - [Counting wins](#counting-wins)
  - [How to join tables](#how-to-join-tables)
    - [Joining all tables](#joining-all-tables)
  - [Example queries](#example-queries)
    - [Films with most wins](#films-with-most-wins)
    - [People with most nominations](#people-with-most-nominations)
    - [Films nominated in all Acting categories](#films-nominated-in-all-acting-categories)
    - [People with longest nomination streaks](#people-with-longest-nomination-streaks)
    - [People with most nominations before winning an award](#people-with-most-nominations-before-winning-an-award)
  - [Extending oscy](#extending-oscy)

## Requirements

- PostgreSQL 13+

## Schema

All columns have the constraint NOT NULL unless otherwise specified.

### Enums

- `award_type` defines the awards ceremonies stored in the database
- `entity_type` defines the kinds of entities stored in the database
- `update_type` defines the states that a particular ceremony's data can be in:
  `nominations` indicates that the ceremony's nominations have been added;
  `unofficial` indicates that the ceremony has finished and preliminary results
  have been added; `official` indicates that official results have been
  published and added

| type        | values                                    |
| ----------- | ----------------------------------------- |
| award_type  | 'oscar', 'emmy'                           |
| entity_type | 'person', 'company', 'country', 'network' |
| update_type | 'nominations', 'unofficial', 'official'   |

### Ceremonies

#### editions

Each ceremony gets 1 entry.

| column        | type               | notes                  | example    |
| ------------- | ------------------ | ---------------------- | ---------- |
| id            | serial PRIMARY KEY | auto-incrementing PK   | 1          |
| award         | award_type         | enum                   | 'oscar'    |
| iteration     | integer            | ceremony iteration     | 96         |
| official_year | varchar(10)        | official ceremony year | '1927/28'  |
| ceremony_date | date               | ceremony date          | 2024-03-10 |

### Categories

oscy defines three levels in the category hierarchy, from broad to narrow:
_category groups_, _categories_, and _category names_.

_Category groups_ group related categories. A single category can go by
different names in different years. _Category name_ refers to the actual name
used at a given ceremony, while _category_ refers to the underlying category,
which remains unchanged. Categories are not required to belong to a category
group.

For example, the category group "Acting" includes the categories "Actor",
"Supporting Actor", "Actress", and "Supporting Actress". The category "Actor"
includes the category names "Best Actor" and "Best Actor in a Leading Role".

This hierarchy allows oscy to compute aggregate stats at each level, and
reconstruct a category's name history.

#### category_groups

Each category group (ex. 'Acting', 'Writing', etc.) gets 1 entry.

| column | type               | notes                | example  |
| ------ | ------------------ | -------------------- | -------- |
| id     | serial PRIMARY KEY | auto-incrementing PK | 1        |
| award  | award_type         | enum                 | 'oscar'  |
| name   | text               | category group       | 'Acting' |

#### categories

Each category (ex. 'Actor', 'Actress', etc.) gets 1 entry.

| column            | type               | notes                                         | example |
| ----------------- | ------------------ | --------------------------------------------- | ------- |
| id                | serial PRIMARY KEY | auto-incrementing PK                          | 1       |
| award             | award_type         | enum                                          | 'oscar' |
| name              | text               | category                                      | 'Actor' |
| category_group_id | integer (nullable) | FK to [category_groups(id)](#category_groups) |         |

#### category_names

Each category name (ex. 'ACTOR', 'ACTOR IN A LEADING ROLE', etc.) gets 1 entry.

| column        | type               | notes                                 | example      |
| ------------- | ------------------ | ------------------------------------- | ------------ |
| id            | serial PRIMARY KEY | auto-incrementing PK                  | 1            |
| award         | award_type         | enum                                  | 'oscar'      |
| official_name | text               | name according to official source     | 'ACTOR'      |
| common_name   | text               | commonly used name                    | 'Best Actor' |
| category_id   | integer            | FK to [categories(id)](#categories-1) |              |

#### editions_category_names

Relates ceremonies to category names used at that ceremony. Each
ceremony/category name combination gets 1 entry.

| column           | type               | notes                                       | example |
| ---------------- | ------------------ | ------------------------------------------- | ------- |
| id               | serial PRIMARY KEY | auto-incrementing PK                        | 1       |
| edition_id       | integer            | FK to [editions(id)](#editions)             |         |
| category_name_id | integer            | FK to [category_names(id)](#category_names) |         |

### Entities & Titles

An entity can be a person, company, country, or network (for Emmys). A title is
a film or television program.

> [!NOTE]
>
> Each entity and title has been matched to its corresponding IMDb id, where
> available. If no matching IMDb id exists, a manual id has been assigned, whose
> third character is an underscore ('\_'). For countries, the IMDb id is
> assigned a 4-character string: 'cc' followed by the
> [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country
> code (ex. 'ccIT' for Italy).

Entity and title names are as listed by the official awards source. For entities
with names that have changed over time, their most recent listed name is
(usually) the one found in the entities table.

#### entities

Each unique entity gets 1 entry.

| column  | type               | notes                | example          |
| ------- | ------------------ | -------------------- | ---------------- |
| id      | serial PRIMARY KEY | auto-incrementing PK | 1                |
| imdb_id | text UNIQUE        | IMDb id              | 'nm0000123'      |
| type    | entity_type        | enum                 | 'person'         |
| name    | text               | name of entity       | 'George Clooney' |

#### titles

Each title gets 1 entry.

| column  | type               | notes                | example       |
| ------- | ------------------ | -------------------- | ------------- |
| id      | serial PRIMARY KEY | auto-incrementing PK | 1             |
| imdb_id | text UNIQUE        | IMDb id              | 'tt16426418'  |
| award   | award_type         | enum                 | 'oscar'       |
| title   | text               | name of film/program | 'Challengers' |

### Nominations

#### nominees

Each nomination gets 1 entry. For nominations involving multiple titles,
`winner` is TRUE if any title within the nomination won. `stat` is TRUE if the
nomination is official and at least one nominee in the same category did not
win.

| column           | type               | notes                                                                  | example                  |
| ---------------- | ------------------ | ---------------------------------------------------------------------- | ------------------------ |
| id               | serial PRIMARY KEY | auto-incrementing PK                                                   | 1                        |
| award            | award_type         | enum                                                                   | 'oscar'                  |
| edition_id       | integer            | FK to [editions(id)](#editions)                                        |                          |
| category_name_id | integer            | FK to [category_names(id)](#category_names)                            |                          |
| statement        | text               | official nomination statement                                          | 'Written by Celine Song' |
| is_person        | boolean            | whether nominee is primarly a person (only TRUE for Acting categories) | FALSE                    |
| pending          | boolean            | whether ceremony results are pending                                   | FALSE                    |
| winner           | boolean            | whether this nominee won the category                                  | FALSE                    |
| note             | text               | official nomination note                                               | ''                       |
| official         | boolean            | whether this nomination is considered official                         | TRUE                     |
| stat             | boolean            | whether this nomination counts toward aggregate nomination stats       | TRUE                     |

#### nominees_titles

Relates nominations to their titles. Each nomination/title combination gets 1
entry. A single nomination can have multiple entries in this table if multiple
titles are listed on the nomination. In some cases, nominations do not have
_any_ associated titles. `winner` is only relevant for the 3rd Oscars.

| column     | type               | notes                                                                               | example          |
| ---------- | ------------------ | ----------------------------------------------------------------------------------- | ---------------- |
| id         | serial PRIMARY KEY | auto-incrementing PK                                                                | 1                |
| nominee_id | integer            | FK to [nominees(id)](#nominees)                                                     |                  |
| title_id   | integer            | FK to [titles(id)](#titles)                                                         |                  |
| detail     | text[]             | characters, song titles, or dance numbers associated with this nomination and title | {"I'm Just Ken"} |
| winner     | boolean            | whether this particular title within the nomination won                             | FALSE            |

#### nominees_entities

Relates nominations to their entities. Each nomination/entity combination gets 1
entry. A single nomination can have multiple entries in this table if multiple
entities are listed on the nomination. In some cases, nominations do not have
_any_ associated entities. `role` is only relevant for Emmy nominations.

| column        | type               | notes                                                     | example      |
| ------------- | ------------------ | --------------------------------------------------------- | ------------ |
| id            | serial PRIMARY KEY | auto-incrementing PK                                      | 1            |
| nominee_id    | integer            | FK to [nominees(id)](#nominees)                           |              |
| entity_id     | integer            | FK to [entities(id)](#entities)                           |              |
| name          | text               | name of entity listed on this nomination (could be alias) | 'P.H. Vazak' |
| statement_ind | integer            | start index of name in nomination statement               | 0            |
| role          | text               | entity's role on set                                      | ''           |

### Other tables

#### current_versions

Each award type gets at most one entry, which defines the current version of
that award's data via a tag. This entry is updated alongside any data update.
The tag is useful for caching and cache busting: the API includes it as an
`ETag` header in responses, and Next.js uses it to make versioned API requests.

The format of the tag is currently
`'<award_abbrev><iteration><update_stage_abbrev><timestamp>'` where:

- `<award_abbrev>` is the award (`o` for Oscars, `e` for Emmys)
- `<iteration>` is the current iteration of the award
- `<update_stage_abbrev>` is the current update stage within the iteration (`n`
  for nominations, `u` for unofficial results, `o` for official results)
- `<timestamp>` is the update timestamp (in Unix format) of the data to the
  nearest second

| column       | type               | notes                                   | example                       |
| ------------ | ------------------ | --------------------------------------- | ----------------------------- |
| id           | serial PRIMARY KEY | auto-incrementing PK                    | 1                             |
| award        | award_type UNIQUE  | enum                                    | 'oscar'                       |
| iteration    | integer            | current ceremony iteration              | 98                            |
| update_stage | update_type        | enum                                    | 'unofficial'                  |
| updated_at   | timestamptz        | update timestamp                        | 2026-03-16 19:00:00.000000-04 |
| tag          | text               | string that uniquely identifies version | 'o98u1773702000'              |

## Usage

Because the rules, format, and categories of the Academy Awards have changed
significantly over time, there are many quirks and edge cases to consider when
querying. This is one of the reasons the
[API](https://oscy.evanxiong.com/api/docs) exists, and why I recommend using the
API whenever possible, especially for simpler queries.

If the API does not fit your needs, or you want to issue your own SQL queries,
read the following sections to avoid later frustration.

### How to count nominations and wins

#### Counting nominations

**The existence of an entity or title in this database alone is not enough to
say that it received any official nominations.**

The `stat` column in `nominees` indicates whether a nomination should count
toward aggregate nomination stats. The column is TRUE if the nomination is
official AND the category is competitive (i.e., there is at least one
non-winning nominee in the category).

> [!WARNING]
>
> Because nominations only count if they are official and competitive, there may
> be cases where an entity or title has more wins than nominations (or even
> multiple wins and 0 nominations). If you want to divide by number of
> nominations, you should have special logic to handle these cases.

#### Counting wins

The `winner` column in `nominees` indicates whether a nomination won its
category. The column is TRUE if any title associated with the nomination won.

> [!NOTE]
>
> Some categories have had multiple winners in the same ceremony, either by
> design, or due to ties in voting.

For nominations with multiple titles, the `winner` column of `nominees_titles`
indicates whether the specific title within the nomination won. At the 3rd
Academy Awards, the winners of Best Actor and Best Actress were each awarded for
their performance in only one of the two films they were nominated for. In all
other cases, the `winner` columns of `nominees` and `nominees_titles` should be
in agreement for the same nomination. To cover all cases, use
`nominees_titles.winner` to count wins for titles, and `nominees.winner` to
count wins for entities.

> [!IMPORTANT]
>
> Use `nominees_titles.winner` to count wins for titles, and `nominees.winner`
> to count wins for entities.

### How to join tables

Since the data is fairly normalized, you'll have to join a lot when performing
queries.

#### Joining all tables

To give you a more concrete idea of how the tables are related to each other,
let's join all 10 data tables.

> [!IMPORTANT]
>
> Some nominations have no associated titles, or no associated entities; if you
> are interested in retrieving nominations (and not _only_ titles or _only_
> entities), you'll have to use an outer join to include these nominations in
> the output.

This query will return one entry per nomination/entity/title combination across
all categories and editions. It includes all nominations, regardless of whether
they are official or competitive.

```sql
SELECT *
FROM category_names cn
JOIN categories c ON c.id = cn.category_id
JOIN category_groups cg ON cg.id = c.category_group_id
JOIN editions_category_names ecn ON ecn.category_name_id = cn.id
JOIN editions e ON e.id = ecn.edition_id
JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
LEFT JOIN nominees_entities ne ON ne.nominee_id = n.id
LEFT JOIN entities en ON en.id = ne.entity_id
LEFT JOIN nominees_titles nt ON nt.nominee_id = n.id
LEFT JOIN titles t ON t.id = nt.title_id;
```

> [!NOTE]
>
> Fortunately, there are no nominations associated with >1 entity AND >1 title.
> This can be verified with the following query, which should return no results:
>
> <details>
> <summary>Show query</summary>
>
> ```sql
> SELECT n.id, COUNT(DISTINCT en.id) AS entity_count, COUNT(DISTINCT t.id) AS title_count
> FROM category_names cn
> JOIN categories c ON c.id = cn.category_id
> JOIN category_groups cg ON cg.id = c.category_group_id
> JOIN editions_category_names ecn ON ecn.category_name_id = cn.id
> JOIN editions e ON e.id = ecn.edition_id
> JOIN nominees n ON n.edition_id = e.id AND n.category_name_id = cn.id
> LEFT JOIN nominees_entities ne ON ne.nominee_id = n.id
> LEFT JOIN entities en ON en.id = ne.entity_id
> LEFT JOIN nominees_titles nt ON nt.nominee_id = n.id
> LEFT JOIN titles t ON t.id = nt.title_id
> GROUP BY n.id
> HAVING COUNT(DISTINCT en.id) > 1 AND COUNT(DISTINCT t.id) > 1
> ```
>
> </details>

### Example queries

#### Films with most wins

Note that the `winner` column used is from `nominees_titles` and not from
`nominees` (see [Counting wins](#counting-wins)).

```sql
SELECT t.title, COUNT(*) FILTER (WHERE nt.winner = TRUE) AS wins
FROM nominees n
JOIN nominees_titles nt ON nt.nominee_id = n.id
JOIN titles t ON t.id = nt.title_id
WHERE n.award = 'oscar'
GROUP BY t.id, t.title
ORDER BY wins DESC
LIMIT 10;
```

<details>
<summary>Output (as of Feb. 2025)</summary>

```
                     title                     | wins
-----------------------------------------------+------
 Titanic                                       |   11
 Ben-Hur                                       |   11
 The Lord of the Rings: The Return of the King |   11
 West Side Story                               |   10
 The Last Emperor                              |    9
 The English Patient                           |    9
 Gigi                                          |    9
 Gandhi                                        |    8
 My Fair Lady                                  |    8
 Slumdog Millionaire                           |    8
(10 rows)
```

</details>

#### People with most nominations

```sql
SELECT en.name, COUNT(*) FILTER (WHERE n.stat = TRUE) AS noms
FROM nominees n
JOIN nominees_entities ne ON ne.nominee_id = n.id
JOIN entities en ON en.id = ne.entity_id
WHERE n.award = 'oscar' AND en.type = 'person'
GROUP BY en.id, en.name
ORDER BY noms DESC
LIMIT 10;
```

<details>
<summary>Output (as of Feb. 2025)</summary>

```
      name       | noms
-----------------+------
 Walt Disney     |   59
 John Williams   |   54
 Alfred Newman   |   45
 Cedric Gibbons  |   38
 Edith Head      |   35
 Edwin B. Willis |   32
 Lyle Wheeler    |   29
 Sam Comer       |   26
 Sammy Cahn      |   26
 Andy Nelson     |   25
(10 rows)
```

</details>

#### Films nominated in all Acting categories

The four Acting categories have id 1 (Actor), 2 (Supporting Actor), 3 (Actress),
and 4 (Supporting Actress). The `<@` operator checks whether all elements in the
left-hand array appear in the right-hand array.

```sql
SELECT t.title
FROM nominees n
JOIN nominees_titles nt ON nt.nominee_id = n.id
JOIN titles t ON t.id = nt.title_id
JOIN category_names cn ON cn.id = n.category_name_id
JOIN categories c ON c.id = cn.category_id
WHERE n.award = 'oscar' AND n.stat = TRUE
GROUP BY t.id, t.title
HAVING ARRAY[1,2,3,4] <@ array_agg(c.id);
```

<details>
<summary>Output (as of Feb. 2025)</summary>

```
              title
---------------------------------
 My Man Godfrey
 Mrs. Miniver
 For Whom the Bell Tolls
 Johnny Belinda
 Sunset Blvd.
 A Streetcar Named Desire
 From Here to Eternity
 Who's Afraid of Virginia Woolf?
 Bonnie and Clyde
 Guess Who's Coming to Dinner
 Network
 Coming Home
 Reds
 Silver Linings Playbook
 American Hustle
(15 rows)
```

</details>

#### People with longest nomination streaks

The CTE gets the streak group each person/edition combination belongs to.

```sql
WITH cte AS (
	SELECT
        en.id,
        en.name,
        e.iteration,
        (e.iteration - dense_rank() OVER (PARTITION BY en.id ORDER BY e.iteration)) AS streak_group
	FROM nominees n
	JOIN nominees_entities ne ON ne.nominee_id = n.id
	JOIN entities en ON en.id = ne.entity_id
	JOIN editions e ON e.id = n.edition_id
	WHERE n.award = 'oscar' AND n.stat = TRUE AND en.type = 'person'
	GROUP BY en.id, en.name, e.iteration
	ORDER BY en.name, e.iteration
)
SELECT name, MIN(iteration) AS start_edition, COUNT(*) as streak
FROM cte
GROUP BY id, name, streak_group
ORDER BY streak DESC
LIMIT 10;
```

<details>
<summary>Output (as of Feb. 2025)</summary>

```
         name         | start_edition | streak
----------------------+---------------+--------
 Walt Disney          |            14 |     22
 Alfred Newman        |            10 |     20
 Edith Head           |            21 |     19
 Col. Nathan Levinson |             6 |     14
 Max Steiner          |            11 |     13
 John P. Livadary     |             7 |     13
 Thomas T. Moulton    |             7 |     12
 Hal Pereira          |            25 |     12
 Douglas Shearer      |             7 |     12
 E. H. Hansen         |             7 |     11
(10 rows)
```

</details>

#### People with most nominations before winning an award

The CTE gets the first edition in which each person won.

```sql
WITH first_win AS (
	SELECT DISTINCT ON (en.id) en.id, en.name, e.iteration
	FROM nominees n
	JOIN nominees_entities ne ON ne.nominee_id = n.id
	JOIN entities en ON en.id = ne.entity_id
	JOIN editions e ON e.id = n.edition_id
	WHERE n.award = 'oscar' AND n.winner = TRUE AND en.type = 'person'
	ORDER BY en.id, e.iteration
)
SELECT en.name, COUNT(*) AS noms
FROM nominees n
JOIN nominees_entities ne ON ne.nominee_id = n.id
JOIN entities en ON en.id = ne.entity_id
JOIN editions e ON e.id = n.edition_id
JOIN first_win fw ON fw.id = en.id AND e.iteration < fw.iteration
WHERE n.award = 'oscar' AND n.stat = TRUE AND en.type = 'person'
GROUP BY en.id, en.name
ORDER BY noms DESC
LIMIT 10;
```

<details>
<summary>Output (as of Feb. 2025)</summary>

```
         name         | noms
----------------------+------
 Victor Young         |   20
 Kevin O'Connell      |   20
 Hans Dreier          |   17
 Randy Newman         |   14
 Col. Nathan Levinson |   14
 Roger Deakins        |   13
 Lionel Newman        |   10
 Sammy Cahn           |    9
 Jerry Goldsmith      |    8
 Johnny Mercer        |    8
(10 rows)
```

</details>

### Extending oscy

If you want to perform more advanced queries using data not in this database,
you can use the
[TMDB API](https://developer.themoviedb.org/reference/find-by-id) to fetch info
such as age, gender, genre, language, production company, and more via entity
and title IMDb ids.

> [!WARNING]
>
> Not all entities and titles have a corresponding IMDb entry (see
> [Entities & Titles](#entities--titles)), and not all IMDb entries have a
> corresponding TMDB entry.
