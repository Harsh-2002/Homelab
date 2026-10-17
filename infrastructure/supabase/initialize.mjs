import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';

const root = process.argv[2];
const envPath = path.join(root, '.env');
if (fs.existsSync(envPath) || fs.existsSync(path.join(root, 'volumes/db/data/PG_VERSION'))) {
  throw new Error('Refusing to regenerate secrets for an existing installation');
}
const hex = n => crypto.randomBytes(n).toString('hex');
const base64 = n => crypto.randomBytes(n).toString('base64');
const secret = base64(30);
const { privateKey, publicKey } = crypto.generateKeyPairSync('ec', { namedCurve: 'prime256v1' });
const kid = crypto.randomUUID();
const properties = { kid, use: 'sig', alg: 'ES256', ext: true };
const pub = { ...publicKey.export({ format: 'jwk' }), ...properties, key_ops: ['verify'] };
const priv = { ...privateKey.export({ format: 'jwk' }), ...properties, key_ops: ['sign', 'verify'] };
const oct = { kty: 'oct', k: Buffer.from(secret).toString('base64url'), alg: 'HS256' };
const iat = Math.floor(Date.now() / 1000);
function jwt(role, asymmetric = false) {
  const encode = obj => Buffer.from(JSON.stringify(obj)).toString('base64url');
  const input = `${encode(asymmetric ? { alg: 'ES256', typ: 'JWT', kid } : { alg: 'HS256', typ: 'JWT' })}.${encode({ role, iss: 'supabase', iat, exp: iat + 5 * 365 * 86400 })}`;
  const signature = asymmetric
    ? crypto.sign('sha256', Buffer.from(input), { key: privateKey, dsaEncoding: 'ieee-p1363' })
    : crypto.createHmac('sha256', secret).update(input).digest();
  return `${input}.${signature.toString('base64url')}`;
}
function opaque(prefix) {
  const value = prefix + crypto.randomBytes(17).toString('base64url').slice(0, 22);
  return value + '_' + crypto.createHash('sha256').update('supabase-self-hosted|' + value).digest('base64url').slice(0, 8);
}
const values = {
  JWT_SECRET: secret, ANON_KEY: jwt('anon'), SERVICE_ROLE_KEY: jwt('service_role'),
  SECRET_KEY_BASE: base64(48), REALTIME_DB_ENC_KEY: hex(8), VAULT_ENC_KEY: hex(16),
  PG_META_CRYPTO_KEY: base64(24), POSTGRES_PASSWORD: hex(16), DASHBOARD_PASSWORD: hex(16),
  LOGFLARE_PUBLIC_ACCESS_TOKEN: base64(24), LOGFLARE_PRIVATE_ACCESS_TOKEN: base64(24),
  S3_PROTOCOL_ACCESS_KEY_ID: hex(16), S3_PROTOCOL_ACCESS_KEY_SECRET: hex(32), MINIO_ROOT_PASSWORD: hex(16),
  SUPABASE_PUBLISHABLE_KEY: opaque('sb_publishable_'), SUPABASE_SECRET_KEY: opaque('sb_secret_'),
  ANON_KEY_ASYMMETRIC: jwt('anon', true), SERVICE_ROLE_KEY_ASYMMETRIC: jwt('service_role', true),
  JWT_KEYS: JSON.stringify([priv, oct]), JWT_JWKS: JSON.stringify({ keys: [pub, oct] }),
};
const template = fs.readFileSync(path.join(root, '.env.example'), 'utf8');
const output = template.replace(/^([A-Z][A-Z_0-9]*)=.*$/gm, (line, key) => key in values ? `${key}=${values[key]}` : line);
fs.writeFileSync(envPath, output, { mode: 0o600, flag: 'wx' });
console.log('Generated signing/encryption/API credentials into protected .env; no secrets displayed');
