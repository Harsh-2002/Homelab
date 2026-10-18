-- Delete only Logflare event rows older than seven days, not application data.
CREATE EXTENSION IF NOT EXISTS pg_cron;
SELECT cron.schedule_in_database(
  'homelab-analytics-retention',
  '15 0 * * *',
  $retention$
  DO $body$
  DECLARE item record;
  BEGIN
    FOR item IN SELECT tablename FROM pg_tables
      WHERE schemaname = '_analytics'
        AND tablename ~ '^log_events_[0-9a-f_]{36}$'
    LOOP
      EXECUTE format('DELETE FROM _analytics.%I WHERE timestamp < (now() AT TIME ZONE ''UTC'') - interval ''7 days''', item.tablename);
    END LOOP;
  END $body$;
  $retention$,
  '_supabase'
);
