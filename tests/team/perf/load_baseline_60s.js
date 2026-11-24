import http from 'k6/http';
import { Rate } from 'k6/metrics';
import { check, sleep } from 'k6';

const unexpectedFailures = new Rate('unexpected_failures');

export const options = {
  scenarios: {
    steady_state: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '5s', target: 1 },
        { duration: '60s', target: 1 },
        { duration: '5s', target: 0 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    unexpected_failures: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],    // p95 latency must be under 500ms
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
    tags: { operation: 'quota_availability' },
  };

  // Target Operation: Quota Availability Check (Workflow A)
  const quotaUrl = `${BASE_URL}/api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/`;
  const res = http.get(quotaUrl, params);
  unexpectedFailures.add(res.status !== 200);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has available_number': (r) => r.json().hasOwnProperty('available_number'),
    'response under 500ms': (r) => r.timings.duration < 500,
  });

  sleep(0.3);
}
