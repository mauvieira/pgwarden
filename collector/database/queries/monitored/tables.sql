SELECT
  c.oid AS table_oid,
  n.nspname AS schema_name,
  c.relname AS name,
  obj_description(c.oid, 'pg_class') AS description
FROM
  pg_catalog.pg_class c
  JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE
  c.relkind = 'r'
  AND n.nspname NOT IN (
    'pg_catalog', 'information_schema',
    'pg_toast'
  )
  AND n.nspname NOT LIKE 'pg_temp_%'
ORDER BY
  n.nspname,
  c.relname;
