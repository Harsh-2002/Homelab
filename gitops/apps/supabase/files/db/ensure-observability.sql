-- Required Studio observability dependency, not an optional application extension.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL search_path = public, extensions;
SELECT pg_advisory_xact_lock(hashtext('homelab-supabase-platform-init'));
CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA extensions;
-- CNPG creates this relocatable extension in public when re-enabling it.
-- Keep the existing Supabase extension schema without recreating its objects.
ALTER EXTENSION pg_stat_statements SET SCHEMA extensions;
DO $$
BEGIN
  IF NOT ('pg_stat_statements' = ANY(string_to_array(current_setting('shared_preload_libraries'), ',')))
     OR to_regclass('pg_stat_statements') IS NULL THEN
    RAISE EXCEPTION 'Query Performance requires pg_stat_statements preload and SQL objects';
  END IF;
  -- Exercise the function, not only its catalog entry.
  PERFORM 1 FROM pg_stat_statements LIMIT 1;
END $$;
INSERT INTO homelab_bootstrap.platform_migrations(version)
VALUES ('v4-observability-contract') ON CONFLICT DO NOTHING;
INSERT INTO homelab_bootstrap.platform_migrations(version)
VALUES ('v5-managed-observability-schema') ON CONFLICT DO NOTHING;
COMMIT;
