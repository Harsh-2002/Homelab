#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
test -f .env || { echo 'Missing protected .env; complete initialization first.' >&2; exit 1; }
test -f homelab.env || { echo 'Missing homelab.env; configure VM IP and URLs first.' >&2; exit 1; }
case "${1:-}" in
    up|start|restart)
        test -s compose.images.yml || {
            echo 'Missing image digest lock; resolve and review it before starting.' >&2
            exit 1
        }
        if grep -Eq 'your-super-secret|this_password_is_insecure|fake_mail_' .env; then
            echo 'Upstream example credentials remain. Refusing to start.' >&2
            exit 1
        fi
        ;;
esac
if [ -f compose.images.yml ]; then
    exec docker compose --project-name supabase --env-file .env --env-file homelab.env \
        -f docker-compose.yaml -f docker-compose.logs.yml -f compose.homelab.yaml \
        -f compose.images.yml -f compose.auto-update.yaml -f compose.watchtower.yaml "$@"
fi
exec docker compose --project-name supabase --env-file .env --env-file homelab.env \
    -f docker-compose.yaml -f docker-compose.logs.yml -f compose.homelab.yaml -f compose.auto-update.yaml -f compose.watchtower.yaml "$@"
