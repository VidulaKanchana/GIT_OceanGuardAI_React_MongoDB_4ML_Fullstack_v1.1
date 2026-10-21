import React, { useEffect } from 'react';
import { Box, Alert, Snackbar, Typography } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { useStore } from '../../store/useStore';
import CloudOffIcon from '@mui/icons-material/CloudOff';

export const MainLayout: React.FC = () => {
  const { user, isOnline, pendingSyncCount, setOnlineStatus, refreshPendingSyncCount, activeNotification, clearNotification } = useStore();

  useEffect(() => {
    const handleOnline = () => setOnlineStatus(true);
    const handleOffline = () => setOnlineStatus(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    refreshPendingSyncCount();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: '#070f1e' }}>
      <Navbar />

      {/* Offline Status Persistent Banner */}
      {!isOnline && (
        <Box sx={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', borderBottom: '1px solid #f59e0b', py: 0.8, px: 3, display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <CloudOffIcon sx={{ color: '#f59e0b', fontSize: 20 }} />
          <Typography variant="body2" sx={{ color: '#fbbf24', fontWeight: 600 }}>
            Offshore Offline Mode Active — All created trips, catches, and distress logs are securely persisted in local IndexedDB. {pendingSyncCount > 0 ? `(${pendingSyncCount} operations waiting for shore network)` : ''}
          </Typography>
        </Box>
      )}

      <Box sx={{ display: 'flex', flex: 1 }}>
        {user && <Sidebar />}
        <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, md: 3.5 }, overflowX: 'hidden' }}>
          <Outlet />
        </Box>
      </Box>

      {/* Global Toast Alert */}
      <Snackbar
        open={Boolean(activeNotification)}
        autoHideDuration={5000}
        onClose={clearNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        {activeNotification ? (
          <Alert onClose={clearNotification} severity={activeNotification.severity} sx={{ width: '100%', borderRadius: 2 }}>
            {activeNotification.message}
          </Alert>
        ) : undefined}
      </Snackbar>
    </Box>
  );
};
