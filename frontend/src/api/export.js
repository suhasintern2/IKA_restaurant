// CSV export triggers a browser download of the file returned by
// GET /export, honoring the currently applied filters.

const EXPORT_FILENAME = 'til_entries.csv';

async function toError(response) {
  try {
    const errorData = await response.json();
    if (errorData.detail) return errorData.detail;
    if (errorData.message) return errorData.message;
  } catch {
    // fall through
  }
  return response.statusText || `HTTP ${response.status}`;
}

export async function exportCsv({ restaurant, ticketNumber } = {}) {
  const queryParams = new URLSearchParams();

  if (restaurant) {
    queryParams.append('restaurant', restaurant);
  }

  if (ticketNumber) {
    queryParams.append('ticket_number', ticketNumber);
  }

  const query = queryParams.toString();
  const response = await fetch(`/api/export${query ? `?${query}` : ''}`, {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error(await toError(response));
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = EXPORT_FILENAME;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}