import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],       // Error rate must be under 1%
    http_req_duration: ['p(95)<500'],    // 95% of requests must complete in < 500ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8345';
const TOKEN = __ENV.API_TOKEN;
if (!TOKEN) throw new Error('Set API_TOKEN in the environment; credentials are never embedded in the script.');

export default function () {
  const params = {
    headers: {
      'Authorization': `Token ${TOKEN}`,
      'Accept': 'application/json',
    },
  };

  // 1. Quota Availability check (Workflow A read path)
  const quotaUrl = `${BASE_URL}/api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/`;
  const quotaRes = http.get(quotaUrl, params);

  check(quotaRes, {
    'quota status is 200': (r) => r.status === 200,
    'quota has available_number': (r) => r.json().hasOwnProperty('available_number'),
    'quota response time < 500ms': (r) => r.timings.duration < 500,
  });

  // 2. Items catalog check
  const itemsUrl = `${BASE_URL}/api/v1/organizers/sqe/events/sqe2026/items/`;
  const itemsRes = http.get(itemsUrl, params);

  check(itemsRes, {
    'items status is 200': (r) => r.status === 200,
    'items list returned': (r) => Array.isArray(r.json().results),
  });

  sleep(0.5);
}
