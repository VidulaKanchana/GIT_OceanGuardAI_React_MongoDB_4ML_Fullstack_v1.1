import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { maritimeTheme } from './theme/theme';
import { MainLayout } from './components/layout/MainLayout';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { VesselsPage } from './pages/VesselsPage';
import { TripsPage } from './pages/TripsPage';
import { SafetyC1Page } from './pages/SafetyC1Page';
import { FishingC2Page } from './pages/FishingC2Page';
import { FuelC4Page } from './pages/FuelC4Page';
import { MarketC3Page } from './pages/MarketC3Page';
import { IntegratedTripPlanPage } from './pages/IntegratedTripPlanPage';
import { ObservationsPage } from './pages/ObservationsPage';
import { RescuePage } from './pages/RescuePage';
import { ModelsPage } from './pages/ModelsPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { useStore } from './store/useStore';

const queryClient = new QueryClient();

// Route guard component
const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { user } = useStore();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={maritimeTheme}>
        <CssBaseline />
        <BrowserRouter>
          <Routes>
            {/* Public Layout */}
            <Route element={<MainLayout />}>
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected Workspaces */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/vessels"
                element={
                  <ProtectedRoute>
                    <VesselsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/trips"
                element={
                  <ProtectedRoute>
                    <TripsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/safety-c1"
                element={
                  <ProtectedRoute>
                    <SafetyC1Page />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/fishing-c2"
                element={
                  <ProtectedRoute>
                    <FishingC2Page />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/fuel-c4"
                element={
                  <ProtectedRoute>
                    <FuelC4Page />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/market-c3"
                element={
                  <ProtectedRoute>
                    <MarketC3Page />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/trip-planning"
                element={
                  <ProtectedRoute>
                    <IntegratedTripPlanPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/observations"
                element={
                  <ProtectedRoute>
                    <ObservationsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/rescue"
                element={
                  <ProtectedRoute>
                    <RescuePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/models"
                element={
                  <ProtectedRoute>
                    <ModelsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/datasets"
                element={
                  <ProtectedRoute>
                    <DatasetsPage />
                  </ProtectedRoute>
                }
              />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
