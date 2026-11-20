import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,
  duration: '60s',
  thresholds: {
    http_req_failed: ['rate<0.01'],       // Unexpected failures must be under 1%
    http_req_duration: ['p(95)<500'],    // p95 latency must be under 500ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8345';
const TOKEN = __ENV.API_TOKEN || '2jt4001j30876dpaccansttyaob6srb2j2b2a5yeyuvvx5usl9syzkk5zinarqfq';

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

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has available_number': (r) => r.json().hasOwnProperty('available_number'),
    'response under 500ms': (r) => r.timings.duration < 500,
  });

  sleep(0.3);
}
