import React from 'react';
import { AppBar, Toolbar, Typography, Box, Button, IconButton, Chip, Menu, MenuItem, Tooltip } from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import WavesIcon from '@mui/icons-material/Waves';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import SyncIcon from '@mui/icons-material/Sync';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import SosIcon from '@mui/icons-material/Sos';
import { useStore } from '../../store/useStore';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { user, role, isOnline, pendingSyncCount, logout, syncOfflineQueue } = useStore();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleClose();
    logout();
    navigate('/login');
  };

  return (
    <AppBar position="sticky" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar sx={{ justifyContent: 'space-between', minHeight: 64 }}>
        {/* Brand */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, cursor: 'pointer' }} onClick={() => navigate(user ? '/dashboard' : '/')}>
          <WavesIcon sx={{ color: '#00b4d8', fontSize: 32 }} />
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800, color: '#f8fafc', lineHeight: 1.1 }}>
              OceanGuard <span style={{ color: '#00b4d8' }}>AI</span>
            </Typography>
            <Typography variant="caption" sx={{ color: '#94a3b8', fontSize: '0.65rem', letterSpacing: '0.05em' }}>
              OFFLINE-FIRST MARITIME INTELLIGENCE
            </Typography>
          </Box>
        </Box>

        {/* Center / Right controls */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {/* Connectivity Status Badge */}
          {isOnline ? (
            <Tooltip title="Connected to shore internet network">
              <Chip
                icon={<WifiIcon style={{ color: '#10b981' }} />}
                label={pendingSyncCount > 0 ? `Syncing (${pendingSyncCount})` : "Shore Online"}
                size="small"
                variant="outlined"
                sx={{ borderColor: 'rgba(16, 185, 129, 0.4)', color: '#34d399', fontWeight: 600, fontSize: '0.75rem' }}
                onClick={() => syncOfflineQueue()}
              />
            </Tooltip>
          ) : (
            <Tooltip title="Operating offline in sea mode. Data persisted locally in IndexedDB.">
              <Chip
                icon={<WifiOffIcon style={{ color: '#f59e0b' }} />}
                label={pendingSyncCount > 0 ? `Offline (${pendingSyncCount} queued)` : "Offshore Mode"}
                size="small"
                sx={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', borderColor: '#f59e0b', fontWeight: 600, fontSize: '0.75rem' }}
              />
            </Tooltip>
          )}

          {user ? (
            <>
              {/* Emergency SOS Quick Button */}
              <Button
                variant="contained"
                color="error"
                size="small"
                startIcon={<SosIcon />}
                component={RouterLink}
                to="/rescue"
                sx={{ fontWeight: 700, borderRadius: 2 }}
              >
                SOS Distress
              </Button>

              {/* Role Indicator */}
              <Chip
                label={role?.toUpperCase()}
                size="small"
                sx={{
                  backgroundColor: role === 'admin' ? '#7c3aed' : role === 'researcher' ? '#0284c7' : '#0d9488',
                  color: '#fff',
                  fontWeight: 700,
                  fontSize: '0.7rem'
                }}
              />

              {/* Profile Menu */}
              <IconButton onClick={handleMenu} sx={{ color: '#94a3b8', p: 0.5 }}>
                <AccountCircleIcon sx={{ fontSize: 32 }} />
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleClose}
                PaperProps={{
                  sx: { backgroundColor: '#0f1d36', border: '1px solid rgba(255,255,255,0.1)' }
                }}
              >
                <MenuItem disabled sx={{ color: '#94a3b8' }}>
                  {user.full_name} ({user.email})
                </MenuItem>
                <MenuItem component={RouterLink} to="/dashboard" onClick={handleClose}>
                  Main Dashboard
                </MenuItem>
                <MenuItem component={RouterLink} to="/vessels" onClick={handleClose}>
                  Vessel Fleet
                </MenuItem>
                <MenuItem component={RouterLink} to="/observations" onClick={handleClose}>
                  Field Observations
                </MenuItem>
                <MenuItem onClick={handleLogout} sx={{ color: '#ef4444' }}>
                  Sign Out
                </MenuItem>
              </Menu>
            </>
          ) : (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button color="inherit" component={RouterLink} to="/login">
                Sign In
              </Button>
              <Button variant="contained" color="primary" component={RouterLink} to="/register">
                Register
              </Button>
            </Box>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};
