import { apiFetchFormData } from './client';

// One POST /upload per file (each returns a per-image success/failure state
// in the UI). The backend reads a single multipart field named `file`.
async function uploadImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  return apiFetchFormData('/upload', formData);
}

// Upload one or more images. Returns an array of backend responses in the
// same order as the input files.
export async function uploadImages(files) {
  return Promise.all(files.map(uploadImage));
}

export async function uploadTicketScreenshotBatch(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  return apiFetchFormData('/upload/tickets', formData);
}

export async function uploadDocketImageBatch(files) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  return apiFetchFormData('/upload/dockets', formData);
}