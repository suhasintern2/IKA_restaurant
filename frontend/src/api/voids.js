import { apiFetch } from './client';

export function getVoidReconciliation() {
  return apiFetch('/reconcile/voids');
}

export async function exportVoidReconciliation() {
  const response = await fetch('/api/reconcile/voids/export');
  if (!response.ok) {
    throw new Error(`Void export failed: ${response.statusText}`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'void-reconciliation.csv';
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}