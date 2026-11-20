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
  const token = '2jt4001j30876dpaccansttyaob6srb2j2b2a5yeyuvvx5usl9syzkk5zinarqfq';
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
