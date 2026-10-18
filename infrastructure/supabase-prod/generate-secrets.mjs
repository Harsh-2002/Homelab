import crypto from 'node:crypto';
if (process.stdout.isTTY) throw new Error('Private output must be captured by bootstrap.py, not printed');
const hex = n => crypto.randomBytes(n).toString('hex');
const b64 = n => crypto.randomBytes(n).toString('base64');
const secret = b64(30);
const { privateKey, publicKey } = crypto.generateKeyPairSync('ec', { namedCurve: 'prime256v1' });
const kid = crypto.randomUUID();
const properties = { kid, use: 'sig', alg: 'ES256', ext: true };
const pub = { ...publicKey.export({ format: 'jwk' }), ...properties, key_ops: ['verify'] };
const priv = { ...privateKey.export({ format: 'jwk' }), ...properties, key_ops: ['sign','verify'] };
const oct = { kty:'oct', k:Buffer.from(secret).toString('base64url'), alg:'HS256' };
const iat = Math.floor(Date.now()/1000);
function jwt(role, asymmetric=false) {
  const encode = value => Buffer.from(JSON.stringify(value)).toString('base64url');
  const input = encode(asymmetric?{alg:'ES256',typ:'JWT',kid}:{alg:'HS256',typ:'JWT'})+'.'+encode({role,iss:'supabase',iat,exp:iat+5*365*86400});
  const signature = asymmetric?crypto.sign('sha256',Buffer.from(input),{key:privateKey,dsaEncoding:'ieee-p1363'}):crypto.createHmac('sha256',secret).update(input).digest();
  return input+'.'+signature.toString('base64url');
}
function opaque(prefix) {
  const value=prefix+crypto.randomBytes(17).toString('base64url').slice(0,22);
  return value+'_'+crypto.createHash('sha256').update('supabase-self-hosted|'+value).digest('base64url').slice(0,8);
}
console.log(JSON.stringify({
  jwtSecret:secret,anonKey:jwt('anon'),serviceKey:jwt('service_role'),
  publishableKey:opaque('sb_publishable_'),secretKey:opaque('sb_secret_'),
  anonKeyAsymmetric:jwt('anon',true),serviceRoleKeyAsymmetric:jwt('service_role',true),
  jwtKeys:JSON.stringify([priv,oct]),jwtJwks:JSON.stringify({keys:[pub,oct]}),
  password:hex(24),database:'postgres',username:'supabase',dashboardPassword:hex(24),
  publicAccessToken:b64(24),privateAccessToken:b64(24),secretKeyBase:b64(48),
  dbEncKey:hex(8),cryptoKey:b64(24),rootKey:hex(32),
  keyId:hex(16),accessKey:hex(32),mcpKey:'sb_mcp_'+crypto.randomBytes(32).toString('base64url'),
}));
