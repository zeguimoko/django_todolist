import http from 'k6/http';
import { check, sleep } from 'k6';
import { htmlReport } from 'https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js';

const BASE_URL = __ENV.BASE_URL || 'http://0.0.0.0:8000';
const SESSION_ID = __ENV.SESSION_ID || '96m7uht1y8um3p25bdoi97yfw1bk5tb9';

const SUCCESS_USER = __ENV.SUCCESS_USER || 'aty';
const SUCCESS_PASS = __ENV.SUCCESS_PASS || 'aty';
const FAIL_USER = __ENV.FAIL_USER || 'abc';
const FAIL_PASS = __ENV.FAIL_PASS || 'ererrer';

const loginUrl = `${BASE_URL}/accounts/login/`;
const baseHeaders = {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Cookie': `sessionid=${SESSION_ID}`,
};

export const options = {
  // iterations: 100,
  // vus: 10,
  stages: [
    { duration: '20s', target: 20 },
    { duration: '20s', target: 5 },
    { duration: '30s', target: 40 },
    { duration: '25s', target: 20 },
  ],
};

export function handleSummary(data) {
  return {
    'summary.html': htmlReport(data),
  };
}

export default function () {
  const successPayload =
    `username=${encodeURIComponent(SUCCESS_USER)}` +
    `&password=${encodeURIComponent(SUCCESS_PASS)}`;

  const failPayload =
    `username=${encodeURIComponent(FAIL_USER)}` +
    `&password=${encodeURIComponent(FAIL_PASS)}`;

  const requests = [
    {
      method: 'POST',
      url: loginUrl,
      body: successPayload,
      params: {
        headers: baseHeaders,
        redirects: 10, // max redirects
      },
    },
    {
      method: 'POST',
      url: loginUrl,
      body: failPayload,
      params: {
        headers: baseHeaders,
        redirects: 10,
      },
    },  
    {
      method: 'POST',
      url: loginUrl,
      body: failPayload,
      params: {
        headers: baseHeaders,
        redirects: 10,
      },
    },    
  ];

  const responses = http.batch(requests);

  check(responses[0], {
    'login_success: status 200/302': (r) => r.status === 200 || r.status === 302,
  });

  check(responses[1], {
    'login_fail: status 200': (r) => r.status === 200,
  });

  check(responses, {
    'batch sem erro 5xx': (rs) => rs.every((r) => r.status < 500),
  });

  sleep(1);
}
