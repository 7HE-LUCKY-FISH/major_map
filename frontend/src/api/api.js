// A small wrapper around fetch to make backend calls easier to manage
const BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, options);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed: ${res.status} ${res.statusText} - ${text}`);
  }
  return res.json();
}

export function getHealth() {
  return request(`/health`);
}

// add other API calls here, examples:
export function fetchSchedules(payload) {
  return request(`/schedules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function fetchCourses() {
  return request(`/courses`);
}

// API end points
