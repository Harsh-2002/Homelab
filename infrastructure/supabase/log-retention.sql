-- Bound local analytics growth to seven days. Only Logflare event tables.
DO $$
DECLARE item record;
BEGIN
  FOR item IN SELECT tablename FROM pg_tables
    WHERE schemaname = '_analytics'
      AND tablename ~ '^log_events_[0-9a-f_]{36}$'
  LOOP
    EXECUTE format('DELETE FROM _analytics.%I WHERE timestamp < (now() AT TIME ZONE ''UTC'') - interval ''7 days''', item.tablename);
  END LOOP;
END $$;
