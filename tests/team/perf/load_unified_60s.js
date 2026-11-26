import http from 'k6/http';
import { Rate } from 'k6/metrics';
import { check, sleep } from 'k6';

// Mark HTTP 200, 201, and expected domain quota-exhaustion 400 as expected responses
http.setResponseCallback(http.expectedStatuses(200, 201, 400));

const unexpectedFailures = new Rate('unexpected_failures');

const TARGET_VUS = parseInt(__ENV.VUS || '1', 10);
const RAMP_DURATION = __ENV.RAMP || (TARGET_VUS === 1 ? '5s' : '10s');
const STEADY_DURATION = __ENV.STEADY || '60s';

export const options = {
  scenarios: {
    steady_state: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: RAMP_DURATION, target: TARGET_VUS },
        { duration: STEADY_DURATION, target: TARGET_VUS },
        { duration: RAMP_DURATION, target: 0 },
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

  // 1. Quota Availability Read (Workflow A)
  const quotaUrl = `${BASE_URL}/api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/`;
  const quotaRes = http.get(quotaUrl, { headers: headers, tags: { type: 'read' } });
  unexpectedFailures.add(quotaRes.status !== 200);

  check(quotaRes, {
    'read status is 200': (r) => r.status === 200,
    'has available_number': (r) => r.json().hasOwnProperty('available_number'),
  });

  // 2. Idempotent Order Placement Write (Workflow A)
  const ordersUrl = `${BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/`;
  const payload = JSON.stringify({
    email: `load_buyer_${uniqueId}@sqe.local`,
    locale: 'en',
    sales_channel: 'web',
    positions: [
      {
        item: 1,
        price: '50.00',
        attendee_name: `Load VU ${vuId}`,
      },
    ],
  });

  const orderHeaders = Object.assign({}, headers, {
    'X-Idempotency-Key': `k6_unified_${TARGET_VUS}vu_${uniqueId}`,
  });

  const orderRes = http.post(ordersUrl, payload, { headers: orderHeaders, tags: { type: 'write' } });
  unexpectedFailures.add(orderRes.status !== 201 && orderRes.status !== 400);

  check(orderRes, {
    'expected status 201 or 400': (r) => r.status === 201 || r.status === 400,
    'no internal server error 5xx': (r) => r.status < 500,
  });

  sleep(0.5);
}
