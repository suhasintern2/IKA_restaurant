import { apiFetch } from './client';

// Fetch table rows, optionally filtered by restaurant and/or ticket number.
// Field names and query params match the backend exactly (restaurant,
// ticket_number). The backend matches both filters by exact value.
export async function getEntries({ restaurant, ticketNumber } = {}) {
  const queryParams = new URLSearchParams();

  if (restaurant) {
    queryParams.append('restaurant', restaurant);
  }

  if (ticketNumber) {
    queryParams.append('ticket_number', ticketNumber);
  }

  const query = queryParams.toString();
  return apiFetch(`/entries${query ? `?${query}` : ''}`);
}

// Update an entry's description and/or status. Backend accepts
// { description, status } on PATCH /entries/{id} and returns the updated row.
export async function updateEntry(id, updates) {
  return apiFetch(`/entries/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}