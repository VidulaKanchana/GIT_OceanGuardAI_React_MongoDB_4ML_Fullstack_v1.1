import { create } from 'zustand';
import type { User, UserRole } from '../types';
import { getPendingSyncQueue, removeQueueItem } from '../offline/db';
import { apiClient } from '../services/api';

interface AppState {
  user: User | null;
  role: UserRole | null;
  isOnline: boolean;
  pendingSyncCount: number;
  activeNotification: { message: string; severity: 'success' | 'warning' | 'error' | 'info' } | null;
  
  setUser: (user: User | null, role: UserRole | null) => void;
  logout: () => void;
  setOnlineStatus: (isOnline: boolean) => void;
  showNotification: (message: string, severity?: 'success' | 'warning' | 'error' | 'info') => void;
  clearNotification: () => void;
  refreshPendingSyncCount: () => Promise<void>;
  syncOfflineQueue: () => Promise<void>;
}

export const useStore = create<AppState>((set, get) => ({
  user: JSON.parse(localStorage.getItem('oceanguard_user') || 'null'),
  role: (localStorage.getItem('oceanguard_role') as UserRole) || null,
  isOnline: navigator.onLine,
  pendingSyncCount: 0,
  activeNotification: null,

  setUser: (user, role) => {
    if (user && role) {
      localStorage.setItem('oceanguard_user', JSON.stringify(user));
      localStorage.setItem('oceanguard_role', role);
    } else {
      localStorage.removeItem('oceanguard_user');
      localStorage.removeItem('oceanguard_role');
      localStorage.removeItem('oceanguard_token');
      localStorage.removeItem('oceanguard_refresh_token');
    }
    set({ user, role });
  },

  logout: () => {
    localStorage.removeItem('oceanguard_user');
    localStorage.removeItem('oceanguard_role');
    localStorage.removeItem('oceanguard_token');
    localStorage.removeItem('oceanguard_refresh_token');
    set({ user: null, role: null });
  },

  setOnlineStatus: (isOnline: boolean) => {
    set({ isOnline });
    if (isOnline) {
      get().syncOfflineQueue();
    }
  },

  showNotification: (message, severity = 'info') => {
    set({ activeNotification: { message, severity } });
  },

  clearNotification: () => {
    set({ activeNotification: null });
  },

  refreshPendingSyncCount: async () => {
    try {
      const items = await getPendingSyncQueue();
      set({ pendingSyncCount: items.length });
    } catch (e) {
      console.error('Failed to get pending sync count:', e);
    }
  },

  syncOfflineQueue: async () => {
    try {
      const items = await getPendingSyncQueue();
      if (items.length === 0) return;

      get().showNotification(`Reconnected to shore network. Synchronizing ${items.length} queued action(s)...`, 'info');
      let successCount = 0;

      for (const item of items) {
        try {
          if (item.method.toLowerCase() === 'post') {
            await apiClient.post(item.endpoint, item.payload);
          } else if (item.method.toLowerCase() === 'patch') {
            await apiClient.patch(item.endpoint, item.payload);
          }
          if (item.id !== undefined) {
            await removeQueueItem(item.id);
            successCount++;
          }
        } catch (syncErr) {
          console.error(`Failed to sync queued item ${item.id}:`, syncErr);
        }
      }

      await get().refreshPendingSyncCount();
      if (successCount > 0) {
        get().showNotification(`Successfully synchronized ${successCount} offline action(s) to cloud database.`, 'success');
      }
    } catch (e) {
      console.error('Error during offline queue sync:', e);
    }
  },
}));
