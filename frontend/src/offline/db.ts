import { openDB, type DBSchema } from 'idb';

interface OceanGuardDBSchema extends DBSchema {
  vessels: {
    key: string;
    value: any;
  };
  trips: {
    key: string;
    value: any;
  };
  cachedPredictions: {
    key: string;
    value: {
      key: string;
      component: string;
      data: any;
      cachedAt: string;
    };
  };
  offlineSyncQueue: {
    key: number;
    value: {
      id?: number;
      endpoint: string;
      method: string;
      payload: any;
      createdAt: string;
      retryCount: number;
    };
    indexes: { 'by-endpoint': string };
  };
}

const DB_NAME = 'oceanguard_offline_v1';
const DB_VERSION = 1;

export async function initOfflineDB() {
  return openDB<OceanGuardDBSchema>(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('vessels')) {
        db.createObjectStore('vessels', { keyPath: 'vessel_id' });
      }
      if (!db.objectStoreNames.contains('trips')) {
        db.createObjectStore('trips', { keyPath: 'trip_id' });
      }
      if (!db.objectStoreNames.contains('cachedPredictions')) {
        db.createObjectStore('cachedPredictions', { keyPath: 'key' });
      }
      if (!db.objectStoreNames.contains('offlineSyncQueue')) {
        const store = db.createObjectStore('offlineSyncQueue', { keyPath: 'id', autoIncrement: true });
        store.createIndex('by-endpoint', 'endpoint');
      }
    },
  });
}

// Queue an action to sync when back online
export async function queueOfflineAction(endpoint: string, method: string, payload: any) {
  const db = await initOfflineDB();
  const item = {
    endpoint,
    method,
    payload,
    createdAt: new Date().toISOString(),
    retryCount: 0,
  };
  const id = await db.add('offlineSyncQueue', item);
  return id;
}

// Get all pending sync items
export async function getPendingSyncQueue() {
  const db = await initOfflineDB();
  return db.getAll('offlineSyncQueue');
}

// Remove item from queue after successful transmission
export async function removeQueueItem(id: number) {
  const db = await initOfflineDB();
  return db.delete('offlineSyncQueue', id);
}

// Cache prediction result
export async function cachePrediction(key: string, component: string, data: any) {
  const db = await initOfflineDB();
  return db.put('cachedPredictions', {
    key,
    component,
    data,
    cachedAt: new Date().toISOString(),
  });
}

// Get cached prediction
export async function getCachedPrediction(key: string) {
  const db = await initOfflineDB();
  return db.get('cachedPredictions', key);
}
