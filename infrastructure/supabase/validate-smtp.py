"""Verify SMTP TLS/login without sending mail or revealing credentials."""
import pathlib
import shlex
import smtplib
import ssl

env = {}
for line in pathlib.Path('/srv/supabase/.env').read_text().splitlines():
    if line and not line.startswith('#') and '=' in line:
        key, value = line.split('=', 1)
        env[key] = shlex.split(value)[0] if value else ''
with smtplib.SMTP(env['SMTP_HOST'], int(env['SMTP_PORT']), timeout=20) as smtp:
    smtp.ehlo()
    smtp.starttls(context=ssl.create_default_context())
    smtp.ehlo()
    smtp.user, smtp.password = env['SMTP_USER'], env['SMTP_PASS']
    code, _ = smtp.auth('LOGIN', smtp.auth_login, initial_response_ok=False)
    assert code == 235
print('PASS: SMTP STARTTLS and authentication; no email sent')
