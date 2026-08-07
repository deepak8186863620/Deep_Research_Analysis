// services/api.js
// PURPOSE: Centralized API client for talking to our FastAPI backend.
// All fetch calls live here — components never call fetch() directly.
// This way if the backend URL changes, we fix it in one place.

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Submit a new research topic.
 * Returns the task object with an `id` to poll for results.
 */
export async function createResearchTask(topic, instructions = '') {
  const res = await fetch(`${BASE_URL}/api/research/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, instructions: instructions || null }),
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
