import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    concurrent_buyers: {
      executor: 'constant-vus',
      vus: 5,
      duration: '30s',
    },
  },
  thresholds: {
    // We expect 201 for initial orders and 400 once quota is exhausted; 500 is prohibited
    'http_req_duration{type:read}': ['p(95)<500'],
    'http_req_duration{type:write}': ['p(95)<1500'],
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

  // 1. Concurrent Read: Check Quota Availability
  const quotaUrl = `${BASE_URL}/api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/`;
  const quotaRes = http.get(quotaUrl, { headers: headers, tags: { type: 'read' } });

  check(quotaRes, {
    'read status is 200': (r) => r.status === 200,
  });

  // 2. Concurrent Write: Place Order competing for finite capacity
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
    'X-Idempotency-Key': `k6_idemp_${uniqueId}`,
  });

  const orderRes = http.post(ordersUrl, payload, { headers: orderHeaders, tags: { type: 'write' } });

  // Status must be either 201 (Created) or 400 (Quota Full). NEVER 500.
  check(orderRes, {
    'order status is 201 or 400 (no 500 error)': (r) => r.status === 201 || r.status === 400,
    'not internal server error': (r) => r.status !== 500,
  });

  sleep(1);
}
