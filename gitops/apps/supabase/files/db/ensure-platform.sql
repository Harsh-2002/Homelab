-- Reconcile the official Docker init overlays omitted by the original CNPG bootstrap.
-- Session lock also covers the upstream webhook script's own transaction.
SELECT pg_advisory_lock(hashtext('homelab-supabase-platform-init'));
SELECT to_regnamespace('supabase_functions') IS NULL AS webhooks_missing \gset
\if :webhooks_missing
  \i /seed/98-webhooks.sql
\endif

BEGIN;
SET LOCAL lock_timeout = '5s';
\i /seed/99-roles.sql
\i /seed/99-jwt.sql
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_net')
     OR to_regprocedure('supabase_functions.http_request()') IS NULL
     OR to_regclass('supabase_functions.hooks') IS NULL
     OR to_regclass('supabase_functions.migrations') IS NULL THEN
    RAISE EXCEPTION 'Incomplete webhook initialization; refuse to mark migration complete';
  END IF;
END $$;
CREATE TABLE IF NOT EXISTS homelab_bootstrap.platform_migrations (
  version text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO homelab_bootstrap.platform_migrations(version)
VALUES ('v3-official-init-overlays') ON CONFLICT DO NOTHING;
COMMIT;
SELECT pg_advisory_unlock(hashtext('homelab-supabase-platform-init'));
