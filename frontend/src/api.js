import axios from 'axios'

const apiBase = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export const apiClient = axios.create({
  baseURL: apiBase
})

export default apiClient
