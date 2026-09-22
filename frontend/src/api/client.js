// Base API client for TIL System
// Single place that owns the backend base URL, request headers, JSON
// parsing, and error handling. Every other api/* module goes through this.

const BASE_URL = '/api';

// Read an error message out of a failed response body when possible.
async function extractErrorMessage(response) {
  try {
    const errorData = await response.json();
    if (errorData.detail) return typeof errorData.detail === 'string'
      ? errorData.detail
      : JSON.stringify(errorData.detail);
    if (errorData.message) return errorData.message;
  } catch {
    // Body was not JSON — fall through to status text.
  }
  return response.statusText || `HTTP ${response.status}`;
}

async function handleResponse(response) {
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }

  // Empty responses (e.g. 204 No Content) have no body to parse.
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// Base fetch function for JSON endpoints. Sends JSON content-type unless a
// FormData body is given (the browser sets the multipart boundary itself).
export async function apiFetch(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  const config = {
    headers: {
      ...options.headers,
    },
    ...options,
  };

  if (!(options.body instanceof FormData)) {
    config.headers = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
  }

  const response = await fetch(url, config);
  return handleResponse(response);
}

// Convenience wrapper for multipart file uploads.
export async function apiFetchFormData(endpoint, formData, options = {}) {
  return apiFetch(endpoint, {
    method: 'POST',
    body: formData,
    ...options,
  });
}