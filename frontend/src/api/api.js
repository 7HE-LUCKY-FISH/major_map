// A small wrapper around fetch to make backend calls easier to manage
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    credentials: "include",
    ...options,
  });

  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");

  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;

    if (isJson) {
      const data = await res.json().catch(() => null);
      message = data?.detail || data?.message || message;
    } else {
      const text = await res.text().catch(() => "");
      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  if (!isJson) {
    return null;
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

// Register
export function registerUser(payload) {
  return request(`/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// Login
export function loginUser(payload) {
  return request(`/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// Logout
export function logoutUser() {
  return request(`/auth/logout`, {
    method: "POST",
  });
}

// Get current user profile (protected)
export function getProfile() {
  return request(`/auth/profile`);
}

// Update profile
export function updateProfile(payload) {
  return request(`/auth/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getPlannerState() {
  return request(`/auth/planner-state`);
}

export function updatePlannerState(payload) {
  return request(`/auth/planner-state`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
