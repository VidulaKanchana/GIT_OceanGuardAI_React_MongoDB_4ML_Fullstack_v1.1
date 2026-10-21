import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Card, CardContent, Button, Chip, Stack, LinearProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import SecurityIcon from '@mui/icons-material/Security';
import PhishingIcon from '@mui/icons-material/Phishing';
import LocalGasStationIcon from '@mui/icons-material/LocalGasStation';
import StorefrontIcon from '@mui/icons-material/Storefront';
import DirectionsBoatIcon from '@mui/icons-material/DirectionsBoat';
import RouteIcon from '@mui/icons-material/Route';
import HubIcon from '@mui/icons-material/Hub';
import { apiClient } from '../services/api';
import { useStore } from '../store/useStore';
import { FishingMap } from '../components/maps/FishingMap';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useStore();

  const [loading, setLoading] = useState(true);
  const [vessels, setVessels] = useState<any[]>([]);
  const [trips, setTrips] = useState<any[]>([]);
  const [c2Zones, setC2Zones] = useState<any[]>([]);
  const [stats, setStats] = useState({
    activeVessels: 0,
    plannedTrips: 0,
    c1Risk: 'Safe',
    topZone: 'C2Z005',
    avgFuelL: 32.5,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [vRes, tRes, zRes] = await Promise.all([
          apiClient.get('/vessels'),
          apiClient.get('/trips'),
          apiClient.post('/ml/c2/predict', { departure_port_id: 'P_GALLE', target_species: 'SP_YELLOWFIN' })
        ]);

        setVessels(vRes.data);
        setTrips(tRes.data);
        setC2Zones(zRes.data.candidate_zones || []);

        setStats({
          activeVessels: vRes.data.length,
          plannedTrips: tRes.data.filter((t: any) => t.status === 'planned').length,
          c1Risk: 'Safe',
          topZone: zRes.data.candidate_zones?.[0]?.zone_id || 'C2Z005',
          avgFuelL: 34.2,
        });
      } catch (e) {
        console.error('Failed to load dashboard data:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <Box sx={{ pb: 6 }}>
      {/* Header bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: { xs: 'flex-start', md: 'center' }, flexDirection: { xs: 'column', md: 'row' }, gap: 2, mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, color: '#f8fafc' }}>
            Maritime Operations Dashboard
          </Typography>
          <Typography variant="body2" sx={{ color: '#94a3b8' }}>
            Sri Lanka Artisanal Fisheries Fleet Coordination • Southern & Western Zones
          </Typography>
        </Box>
        <Stack direction="row" spacing={1.5}>
          <Button variant="outlined" color="primary" onClick={() => navigate('/trip-planning')} startIcon={<HubIcon />}>
            Integrated Planner
          </Button>
          <Button variant="contained" color="primary" onClick={() => navigate('/trips')} startIcon={<RouteIcon />}>
            New Fishing Trip
          </Button>
        </Stack>
      </Box>

      {loading && <LinearProgress sx={{ mb: 3, borderRadius: 1 }} />}

      {/* KPI Stat Cards */}
      <Grid container spacing={2.5} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="overline" sx={{ color: '#94a3b8', fontWeight: 700 }}>FLEET SUMMARY</Typography>
                <DirectionsBoatIcon sx={{ color: '#00b4d8' }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#f1f5f9' }}>
                {stats.activeVessels}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>
                Registered craft (OFRP / IDAY / IMUL)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="overline" sx={{ color: '#94a3b8', fontWeight: 700 }}>C1 SAFETY STATUS</Typography>
                <SecurityIcon sx={{ color: '#10b981' }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#10b981' }}>
                {stats.c1Risk}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>
                Bi-LSTM DRI Score: 24.5 / 100 (Calm sea)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="overline" sx={{ color: '#94a3b8', fontWeight: 700 }}>C2 BEST ZONE</Typography>
                <PhishingIcon sx={{ color: '#2ec4b6' }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#2ec4b6' }}>
                {stats.topZone}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>
                Tuna HSI: 0.832 (Pareto Rank 1)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                <Typography variant="overline" sx={{ color: '#94a3b8', fontWeight: 700 }}>C4 FUEL BASELINE</Typography>
                <LocalGasStationIcon sx={{ color: '#f59e0b' }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#fbbf24' }}>
                {stats.avgFuelL} L
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>
                PINN requirement + 20% safety margin
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Grid: Interactive Map + Four Components Quick Access */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <Card sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5, color: '#f1f5f9' }}>
              Offshore Fishing Grid & Habitat Suitability (ST-GCN)
            </Typography>
            <FishingMap
              zones={c2Zones}
              selectedZone={c2Zones[0] || null}
              departurePortId="P_GALLE"
              height="440px"
            />
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card sx={{ height: '100%', p: 1 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, color: '#f1f5f9' }}>
                Research System Workspaces
              </Typography>

              <Stack spacing={1.5}>
                <Paper
                  onClick={() => navigate('/safety-c1')}
                  sx={{ p: 1.8, cursor: 'pointer', border: '1px solid rgba(0, 180, 216, 0.2)', backgroundColor: 'rgba(0, 180, 216, 0.05)', '&:hover': { backgroundColor: 'rgba(0, 180, 216, 0.12)' } }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#00b4d8' }}>
                    C1 • Dynamic Vessel Safety Risk
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                    Bidirectional LSTM evaluating hydrodynamic vulnerability & wave steepness.
                  </Typography>
                </Paper>

                <Paper
                  onClick={() => navigate('/fishing-c2')}
                  sx={{ p: 1.8, cursor: 'pointer', border: '1px solid rgba(46, 196, 182, 0.2)', backgroundColor: 'rgba(46, 196, 182, 0.05)', '&:hover': { backgroundColor: 'rgba(46, 196, 182, 0.12)' } }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#2ec4b6' }}>
                    C2 • Fishing Ground Recommendation
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                    Spatiotemporal Graph Convolutional Network & Pareto multi-objective optimization.
                  </Typography>
                </Paper>

                <Paper
                  onClick={() => navigate('/fuel-c4')}
                  sx={{ p: 1.8, cursor: 'pointer', border: '1px solid rgba(245, 158, 11, 0.2)', backgroundColor: 'rgba(245, 158, 11, 0.05)', '&:hover': { backgroundColor: 'rgba(245, 158, 11, 0.12)' } }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#f59e0b' }}>
                    C4 • Physics-Informed Fuel Predictor
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                    PINN constrained by ITTC-1957 skin friction correlation and brake power.
                  </Typography>
                </Paper>

                <Paper
                  onClick={() => navigate('/market-c3')}
                  sx={{ p: 1.8, cursor: 'pointer', border: '1px solid rgba(16, 185, 129, 0.2)', backgroundColor: 'rgba(16, 185, 129, 0.05)', '&:hover': { backgroundColor: 'rgba(16, 185, 129, 0.12)' } }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#10b981' }}>
                    C3 • Fish Market Decisions & Perishability
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                    Temporal Fusion Transformer forecasting + Q10 fish quality degradation kinetics.
                  </Typography>
                </Paper>
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Trips Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Recent Fishing Trips
            </Typography>
            <Button size="small" onClick={() => navigate('/trips')}>View All Trips</Button>
          </Box>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Trip ID</TableCell>
                  <TableCell>Vessel</TableCell>
                  <TableCell>Departure Port</TableCell>
                  <TableCell>Target Zone</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Safety DRI</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {trips.slice(0, 5).map((trip) => (
                  <TableRow key={trip.trip_id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate('/trips')}>
                    <TableCell sx={{ fontWeight: 700, color: '#00b4d8' }}>{trip.trip_id}</TableCell>
                    <TableCell>{trip.vessel_id}</TableCell>
                    <TableCell>{trip.departure_port_id}</TableCell>
                    <TableCell>{trip.target_zone_id}</TableCell>
                    <TableCell>{trip.planned_duration_h} hrs</TableCell>
                    <TableCell>
                      <Chip
                        label={trip.c1_assessment?.risk_label || 'Safe'}
                        size="small"
                        sx={{
                          backgroundColor: trip.c1_assessment?.risk_label === 'Danger' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                          color: trip.c1_assessment?.risk_label === 'Danger' ? '#ef4444' : '#10b981',
                          fontWeight: 700,
                          fontSize: '0.7rem'
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip label={trip.status.toUpperCase()} size="small" variant="outlined" />
                    </TableCell>
                  </TableRow>
                ))}
                {trips.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} sx={{ textAlign: 'center', py: 3, color: '#94a3b8' }}>
                      No trips recorded yet. Click 'New Fishing Trip' to initiate a voyage.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};
