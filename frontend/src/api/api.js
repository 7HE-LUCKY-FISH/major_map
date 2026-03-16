// A small wrapper around fetch to make backend calls easier to manage
const BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    credentials: "include",
    ...options,
  });

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

export function getCourse(courseId) {
  return request(`/courses/${courseId}`);
}

export function listSections(courseId) {
  return request(`/courses/${courseId}/sections`);
}

export function testInstructors(courseNumber) {
  return request(`/courses/instructors/test?course_number=${encodeURIComponent(courseNumber)}`);
}

export function testSlots(courseNumber) {
  return request(`/courses/slots/test?course_number=${encodeURIComponent(courseNumber)}`);
}

export function testCandidates(courseNumber) {
  return request(`/courses/candidates/test?course_number=${encodeURIComponent(courseNumber)}`);
}

// schedule-generation endpoints
export function generateSchedule(payload) {
  return request(`/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function generateScheduleV2(payload) {
  return request(`/schedules/generate_v2`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// API end points
