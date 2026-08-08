// services/api.js
// PURPOSE: Centralized API client for talking to our FastAPI backend.
// All fetch calls live here — components never call fetch() directly.
// This way if the backend URL changes, we fix it in one place.

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Fetch all past research tasks (for sidebar history on page load).
 */
export async function listResearchTasks(limit = 20) {
  const res = await fetch(`${BASE_URL}/api/research/?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to list tasks: ${res.statusText}`);
  return res.json();
}

/**
 * Submit a new research topic.
 * Returns the task object with an `id` to poll for results.
 */
export async function createResearchTask(topic, instructions = '', mode = 'quick') {
  const res = await fetch(`${BASE_URL}/api/research/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, instructions: instructions || null, mode }),
  });
  if (!res.ok) throw new Error(`Failed to create task: ${res.statusText}`);
  return res.json();
}

/**
 * Poll the status and results of a research task by ID.
 * Status can be: "pending" | "processing" | "completed" | "failed"
 */
export async function getResearchTask(taskId) {
  const res = await fetch(`${BASE_URL}/api/research/${taskId}`);
  if (!res.ok) throw new Error(`Failed to fetch task: ${res.statusText}`);
  return res.json();
}

/**
 * Delete a research task from the database.
 */
export async function deleteResearchTask(taskId) {
  const res = await fetch(`${BASE_URL}/api/research/${taskId}`, { method: 'DELETE' });
  if (!res.ok && res.status !== 204) throw new Error(`Failed to delete task: ${res.statusText}`);
}

/**
 * Check if the backend is reachable.
 */
export async function checkHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  return res.ok;
}
