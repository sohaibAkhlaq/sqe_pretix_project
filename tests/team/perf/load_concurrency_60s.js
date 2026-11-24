import http from 'k6/http';
import { Rate } from 'k6/metrics';
import { check, sleep } from 'k6';

const unexpectedFailures = new Rate('unexpected_failures');

export const options = {
  scenarios: {
    concurrent_workload: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 5 },
        { duration: '60s', target: 5 },
        { duration: '10s', target: 0 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    unexpected_failures: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8345';
const TOKEN = __ENV.API_TOKEN;
if (!TOKEN) throw new Error('Set API_TOKEN in the environment; credentials are never embedded in the script.');

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
  unexpectedFailures.add(quotaRes.status !== 200);

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
  unexpectedFailures.add(orderRes.status !== 201 && orderRes.status !== 400);

  // Status must be 201 (Created) or 400 (Quota Full). 500 is an unexpected failure.
  check(orderRes, {
    'expected status 201 or 400': (r) => r.status === 201 || r.status === 400,
    'no internal server error 500': (r) => r.status !== 500,
  });

  sleep(0.5);
}
