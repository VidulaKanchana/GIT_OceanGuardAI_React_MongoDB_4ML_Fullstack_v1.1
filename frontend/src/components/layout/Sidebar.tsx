import React from 'react';
import { Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Typography, Divider } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DirectionsBoatIcon from '@mui/icons-material/DirectionsBoat';
import RouteIcon from '@mui/icons-material/Route';
import SecurityIcon from '@mui/icons-material/Security';
import PhishingIcon from '@mui/icons-material/Phishing';
import LocalGasStationIcon from '@mui/icons-material/LocalGasStation';
import StorefrontIcon from '@mui/icons-material/Storefront';
import HubIcon from '@mui/icons-material/Hub';
import VisibilityIcon from '@mui/icons-material/Visibility';
import MemoryIcon from '@mui/icons-material/Memory';
import StorageIcon from '@mui/icons-material/Storage';
import SosIcon from '@mui/icons-material/Sos';

const DRAWER_WIDTH = 250;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: string;
}

export const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const operations: NavItem[] = [
    { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
    { label: 'Integrated Planner', path: '/trip-planning', icon: <HubIcon />, badge: 'C1→C4' },
    { label: 'Vessel Fleet', path: '/vessels', icon: <DirectionsBoatIcon /> },
    { label: 'Fishing Trips', path: '/trips', icon: <RouteIcon /> },
    { label: 'SOS Distress Event', path: '/rescue', icon: <SosIcon sx={{ color: '#ef4444' }} /> },
  ];

  const intelligence: NavItem[] = [
    { label: 'C1 Vessel Safety Risk', path: '/safety-c1', icon: <SecurityIcon sx={{ color: '#00b4d8' }} />, badge: 'BiLSTM' },
    { label: 'C2 Fishing Grounds', path: '/fishing-c2', icon: <PhishingIcon sx={{ color: '#2ec4b6' }} />, badge: 'ST-GCN' },
    { label: 'C4 Fuel Prediction', path: '/fuel-c4', icon: <LocalGasStationIcon sx={{ color: '#f59e0b' }} />, badge: 'PINN' },
    { label: 'C3 Market & Decisions', path: '/market-c3', icon: <StorefrontIcon sx={{ color: '#10b981' }} />, badge: 'TFT' },
  ];

  const research: NavItem[] = [
    { label: 'Field Observations', path: '/observations', icon: <VisibilityIcon /> },
    { label: 'Model Registry', path: '/models', icon: <MemoryIcon /> },
    { label: 'Dataset Explorer', path: '/datasets', icon: <StorageIcon /> },
  ];

  const renderSection = (title: string, items: NavItem[]) => (
    <Box sx={{ mb: 2 }}>
      <Typography variant="overline" sx={{ px: 2, color: '#64748b', fontWeight: 700, fontSize: '0.68rem', letterSpacing: '0.08em' }}>
        {title}
      </Typography>
      <List dense sx={{ py: 0.5 }}>
        {items.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                  py: 0.8,
                  backgroundColor: isActive ? 'rgba(0, 180, 216, 0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(0, 180, 216, 0.3)' : '1px solid transparent',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.04)',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: isActive ? '#00b4d8' : '#94a3b8' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.84rem',
                    fontWeight: isActive ? 700 : 500,
                    color: isActive ? '#f8fafc' : '#cbd5e1',
                  }}
                />
                {item.badge && (
                  <Typography
                    variant="caption"
                    sx={{
                      px: 0.8,
                      py: 0.2,
                      borderRadius: 1,
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      backgroundColor: 'rgba(255, 255, 255, 0.08)',
                      color: '#94a3b8',
                    }}
                  >
                    {item.badge}
                  </Typography>
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          backgroundColor: '#070f1e',
          borderRight: '1px solid rgba(255, 255, 255, 0.07)',
          pt: 1.5,
        },
      }}
    >
      {renderSection('Trip Operations', operations)}
      <Divider sx={{ my: 1, borderColor: 'rgba(255, 255, 255, 0.06)' }} />
      {renderSection('AI Research Models', intelligence)}
      <Divider sx={{ my: 1, borderColor: 'rgba(255, 255, 255, 0.06)' }} />
      {renderSection('Science & Governance', research)}
    </Drawer>
  );
};
