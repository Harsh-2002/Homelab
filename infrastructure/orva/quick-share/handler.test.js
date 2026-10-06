const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function fixture() {
  const records = new Map(), objects = new Map();
  let failDelete = false, now = Date.now();
  class Put { constructor(input) { this.input = input; } }
  class Get { constructor(input) { this.input = input; } }
  class Delete { constructor(input) { this.input = input; } }
  class Client {
    async send(command) {
      if (command instanceof Put) objects.set(command.input.Key, command.input.Body);
      if (command instanceof Delete) {
        if (failDelete) throw new Error('storage offline');
        objects.delete(command.input.Key);
      }
      return {};
    }
  }
  const kv = {
    async put(key, value, options) { assert.equal(options.ttlSeconds, 0); records.set(key, value); },
    async delete(key) { records.delete(key); },
    async list() { return {keys: [...records].map(([key, value]) => ({key, value})), nextCursor: ''}; }
  };
  class Clock extends Date { static now() { return now; } }
  const context = {
    exports: {}, Buffer, Date: Clock, AbortSignal,
    console: {error() {}},
    process: {env: {S3_ACCESS_KEY: 'test-only', S3_SECRET_KEY: 'test-only', S3_BUCKET: 'artifact', S3_ENDPOINT: 'https://storage.test'}},
    require(name) {
      if (name === 'orva') return {kv};
      if (name === '@aws-sdk/client-s3') return {S3Client: Client, PutObjectCommand: Put, GetObjectCommand: Get, DeleteObjectCommand: Delete};
      if (name === '@aws-sdk/s3-request-presigner') return {getSignedUrl: async (client, command, options) => `https://storage.test/${command.input.Key}?expiry=${options.expiresIn}`};
      return require(name);
    }
  };
  vm.runInNewContext(fs.readFileSync(__dirname + '/handler.js', 'utf8'), context);
  const request = (body, headers = {}) => context.exports.handler({method: 'POST', body: JSON.stringify(body), headers});
  return {request, records, objects, advance(ms) { now += ms; }, failDelete() { failDelete = true; }};
}

const file = {name: 'test.png', type: 'image/png', size: 3, data: 'YWJj'};

test('default expiry and storage namespace', async () => {
  const f = fixture(), r = await f.request(file);
  assert.equal(r.statusCode, 200);
  assert.equal(r.body.expiresIn, 3600);
  assert.match(r.body.url, /quick-share\/[a-f0-9]{48}\.png/);
  assert.equal([...f.objects.values()][0].toString(), 'abc');
});

test('seven days accepted, longer rejected', async () => {
  const f = fixture();
  assert.equal((await f.request({...file, expiresIn: 604800})).statusCode, 200);
  assert.equal((await f.request({...file, expiresIn: 604801})).statusCode, 400);
  assert.equal((await f.request({...file, expiresIn: 0})).statusCode, 400);
  assert.equal((await f.request({...file, expiresIn: 60.5})).statusCode, 400);
});

test('size, MIME, and base64 validation', async () => {
  const f = fixture();
  assert.equal((await f.request({...file, size: 4194305})).statusCode, 400);
  assert.equal((await f.request({...file, size: 0})).statusCode, 400);
  assert.equal((await f.request({...file, type: 'video/mp4'})).statusCode, 415);
  assert.equal((await f.request({...file, data: '!!!!'})).statusCode, 400);
  assert.equal((await f.request({...file, data: 'YQ=='})).statusCode, 400);
});

test('scheduled cleanup deletes only expired manifest objects', async () => {
  const f = fixture();
  await f.request({...file, expiresIn: 60});
  await f.request({...file, expiresIn: 3600});
  f.advance(61000);
  const r = await f.request({action: 'cleanup'}, {'x-orva-trigger': 'cron'});
  assert.equal(r.statusCode, 200);
  assert.equal(r.body.deleted, 1);
  assert.equal(f.objects.size, 1);
  assert.equal(f.records.size, 1);
});

test('failed deletion keeps manifest for retry', async () => {
  const f = fixture();
  await f.request({...file, expiresIn: 60});
  f.advance(61000); f.failDelete();
  const r = await f.request({action: 'cleanup'}, {'x-orva-trigger': 'cron'});
  assert.equal(r.statusCode, 503);
  assert.equal(f.records.size, 1);
});

test('ordinary HTTP cannot invoke cleanup', async () => {
  assert.equal((await fixture().request({action: 'cleanup'})).statusCode, 403);
});
