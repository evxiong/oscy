# data

## db.sql

Result of calling `pg_dump -O -U <username> <dbname> > db.sql`. To copy this
dumped data to your own database, run the following commands:

```shell
# Create new database called 'oscy'
createdb -U <username> oscy

# Load data into database
psql -X -U <username> -d oscy -f <path to db.sql>
```

## oscars.csv

A CSV containing all joined Oscar nomination data. One row per unique
nomination/entity/title combination.

For more info about these fields, read the
[database documentation in the wiki](https://github.com/evxiong/oscy/wiki/Database).

| field          | description                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| iteration      | edition number                                                                                                |
| official_year  | officially listed ceremony year; indicates release year(s) of films                                           |
| ceremony_date  | date of ceremony, YYYY-MM-DD                                                                                  |
| category_group | category group, ex. Acting                                                                                    |
| category       | category, ex. Actor                                                                                           |
| official_name  | official category name, ex. ACTOR                                                                             |
| common_name    | common category name, ex. Best Actor                                                                          |
| nomination_id  | uniquely identifies each nomination; one nomination may span multiple rows due to multiple entities or titles |
| statement      | official nomination statement                                                                                 |
| pending        | whether ceremony results are pending                                                                          |
| winner         | whether nominee won this category                                                                             |
| official       | whether nomination is official                                                                                |
| stat           | whether nomination counts toward aggregate nomination stats                                                   |
| statement_name | entity name as listed in the official statement (may be alias)                                                |
| statement_ind  | start index of entity name in official statement                                                              |
| entity_imdb_id | IMDb id of entity; may not be a real IMDb id - see wiki for details                                           |
| entity_type    | person, company, or country                                                                                   |
| name           | entity name                                                                                                   |
| title_imdb_id  | IMDb id of title; may not be a real IMDb id - see wiki for details                                            |
| title          | title name                                                                                                    |
| detail         | characters, songs, or dance numbers associated with this title                                                |
| title_winner   | whether this particular title within the nomination won                                                       |
| note           | official nomination note                                                                                      |
