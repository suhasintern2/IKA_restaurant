import { apiFetch } from './client';

async function downloadCsv(endpoint, filename) {
  const response = await fetch(`/api${endpoint}`);
  if (!response.ok) throw new Error(`CSV export failed: ${response.statusText}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function getTickets() {
  return apiFetch('/tickets');
}

export function getDockets() {
  return apiFetch('/dockets');
}

export function exportTickets() {
  return downloadCsv('/tickets/export', 'tickets.csv');
}

export function exportDockets() {
  return downloadCsv('/dockets/export', 'dockets.csv');
}