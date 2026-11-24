import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 1,
  duration: '60s',
  thresholds: {
    http_req_failed: ['rate<0.01'], // < 1% errors
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
  },
};

export default function () {
  const token = __ENV.API_TOKEN;
  if (!token) throw new Error('Set API_TOKEN in the environment; credentials are never embedded in the script.');
  const url = 'http://localhost:8345/api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/';

  const params = {
    headers: {
      'Authorization': `Token ${token}`,
      'Accept': 'application/json',
    },
  };

  const res = http.get(url, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has available count': (r) => r.json().hasOwnProperty('available') || r.json().hasOwnProperty('available_number'),
  });

  sleep(1);
}
