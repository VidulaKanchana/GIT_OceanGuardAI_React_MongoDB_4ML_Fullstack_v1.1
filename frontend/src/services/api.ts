import axios from 'axios';
import { queueOfflineAction } from '../offline/db';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request Interceptor: Attach JWT Bearer Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('oceanguard_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Offline Errors & Token Refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Offline handling: If network error or offline, queue mutations
    if (!navigator.onLine || error.message === 'Network Error') {
      if (originalRequest && ['post', 'put', 'patch', 'delete'].includes(originalRequest.method?.toLowerCase() || '')) {
        console.warn('Network offline. Queuing operation for background synchronization:', originalRequest.url);
        try {
          const payload = typeof originalRequest.data === 'string' ? JSON.parse(originalRequest.data) : originalRequest.data;
          await queueOfflineAction(originalRequest.url, originalRequest.method, payload);
          return Promise.resolve({
            data: {
              _is_offline_queued: true,
              message: 'Action saved offline. It will synchronize automatically upon reconnection.',
            },
            status: 202,
            statusText: 'Accepted Offline',
          });
        } catch (queueErr) {
          console.error('Failed to queue offline operation:', queueErr);
        }
      }
    }

    // Refresh Token handling for 401
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('oceanguard_refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken });
          const newToken = res.data.access_token;
          localStorage.setItem('oceanguard_token', newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        } catch (refreshErr) {
          localStorage.removeItem('oceanguard_token');
          localStorage.removeItem('oceanguard_refresh_token');
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);
