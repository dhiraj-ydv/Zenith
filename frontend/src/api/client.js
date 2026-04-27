/**
 * Zenith API Client — Axios instance configured for the backend.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Vaults ───────────────────────────────────────────
export const vaultsApi = {
  list: () => api.get('/vaults'),
  getActive: () => api.get('/vaults/active'),
  create: (path) => api.post('/vaults', { path }),
  delete: (path) => api.delete('/vaults', { params: { path } }),
}

// ── Notes ────────────────────────────────────────────
export const notesApi = {
  list: (label) => api.get('/notes', { params: label ? { label } : {} }),
  get: (id) => api.get(`/notes/${id}`),
  search: (q) => api.get('/notes/search', { params: { q } }),
  create: (data) => api.post('/notes', data),
  update: (id, data) => api.put(`/notes/${id}`, data),
  rename: (id, newTitle) => api.patch(`/notes/${id}/rename`, { new_title: newTitle }),
  delete: (id) => api.delete(`/notes/${id}`),
}

// ── Labels ───────────────────────────────────────────
export const labelsApi = {
  list: () => api.get('/labels'),
  create: (name) => api.post('/labels', { name }),
  move: (name, newParent) => api.post(`/labels/${encodeURIComponent(name)}/move`, { new_parent: newParent }),
  delete: (name) => api.delete(`/labels/${encodeURIComponent(name)}`),
}

// ── Attachments ──────────────────────────────────────
export const attachmentsApi = {
  list: () => api.get('/attachments'),
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/attachments', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getUrl: (filename) => `/api/attachments/${filename}`,
  gc: () => api.post('/attachments/gc'),
}

// ── Graph ────────────────────────────────────────────
export const graphApi = {
  data: (id) => api.get('/graph/data', { params: { id } }),
  index: () => api.get('/graph/index'),
}

export default api
