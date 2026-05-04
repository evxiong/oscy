# Updating data

Data updates should occur when nominations are released (mid Jan), after the
ceremony (early-mid Mar), and after official results are posted (early-mid Apr).
Use `update.sh` to perform the following actions:

1. Run Python update script
2. Update README
3. Create new SQL dump
4. Create new CSV export
5. Update production cloud db
6. Revalidate production Next.js cache

If there are new or updated category names, manually update
[`backend/db/data/oscar_categories.yaml`](/backend/db/data/oscar_categories.yaml).
If there are new countries, manually update
[`backend/db/data/country_codes.yaml`](/backend/db/data/country_codes.yaml).
