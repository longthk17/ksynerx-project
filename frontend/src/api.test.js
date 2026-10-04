import { test } from 'node:test';
import assert from 'node:assert/strict';
import { request } from './api.js';

test('preserves zero-based pagination, encodes filters, and returns the backend payload', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async url => {
    assert.equal(url, '/inventory-api/product?PageIndex=0&Keyword=A%26B');
    return new Response(JSON.stringify({ results: [], totalCount: 0 }));
  };
  try { assert.deepEqual(await request('inventory', 'product', { params: { PageIndex: 0, Keyword: 'A&B', SKUs: '' } }), { results: [], totalCount: 0 }); }
  finally { globalThis.fetch = original; }
});

test('uploads multipart without overriding the browser boundary and accepts queued jobs', async () => {
  const original = globalThis.fetch;
  const form = new FormData();
  form.append('file', new Blob(['example']), 'products.xlsx');
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/cdm-api/upload-excel');
    assert.equal(options.method, 'POST');
    assert.equal(options.body, form);
    assert.equal(options.headers, undefined);
    return new Response(JSON.stringify({ taskId: 'queued-task', fileName: 'excel_uploads/test.xlsx' }), { status: 202 });
  };
  try { assert.equal((await request('cdm', 'upload-excel', { method: 'POST', body: form })).taskId, 'queued-task'); }
  finally { globalThis.fetch = original; }
});

test('reports backend validation details and invalid proxy responses', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => new Response(JSON.stringify({ errorMessage: 'Invalid data', errors: { sku: ['Already exists'] } }), { status: 400 });
    await assert.rejects(request('inventory', 'product'), /Already exists/);
    globalThis.fetch = async () => new Response('<html>Bad gateway</html>', { status: 502 });
    await assert.rejects(request('cdm', 'health-check'), /HTTP 502/);
  } finally { globalThis.fetch = original; }
});
