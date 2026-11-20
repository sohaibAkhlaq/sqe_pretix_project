import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    concurrent_workload: {
      executor: 'constant-vus',
      vus: 5,
      duration: '60s',
    },
  },
  thresholds: {
    // Unexpected failures (5xx server crashes / connection aborts) must be under 1%
    'http_req_failed{status_5xx:true}': ['rate<0.01'],
    'http_req_duration': ['p(95)<1000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8345';
const TOKEN = __ENV.API_TOKEN || '2jt4001j30876dpaccansttyaob6srb2j2b2a5yeyuvvx5usl9syzkk5zinarqfq';

export default function () {
  const vuId = __VU;
  const iterId = __ITER;
  const uniqueId = `${Date.now()}_vu${vuId}_it${iterId}`;

  const headers = {
    'Authorization': `Token ${TOKEN}`,
    'Accept': 'application/json',
    'Content-Type': 'application/json',
  };

  // 1. Quota Availability read
  const quotaUrl = `${BASE_URL}/api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/`;
  const quotaRes = http.get(quotaUrl, { headers: headers, tags: { type: 'read' } });

  check(quotaRes, {
    'read status is 200': (r) => r.status === 200,
  });

  // 2. Order Placement write competing for finite quota (10 items)
  const ordersUrl = `${BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/`;
  const payload = JSON.stringify({
    email: `load_buyer_${uniqueId}@sqe.local`,
    locale: 'en',
    sales_channel: 'web',
    positions: [
      {
        item: 1,
        price: '50.00',
        attendee_name: `Concurrent VU ${vuId}`,
      },
    ],
  });

  const orderHeaders = Object.assign({}, headers, {
    'X-Idempotency-Key': `k6_60s_${uniqueId}`,
  });

  const orderRes = http.post(ordersUrl, payload, { headers: orderHeaders, tags: { type: 'write' } });

  // Status must be 201 (Created) or 400 (Quota Full). 500 is an unexpected failure.
  check(orderRes, {
    'expected status 201 or 400': (r) => r.status === 201 || r.status === 400,
    'no internal server error 500': (r) => r.status !== 500,
  });

  sleep(0.5);
}
