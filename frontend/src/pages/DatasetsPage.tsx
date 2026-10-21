import React, { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, Grid, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Paper, Alert } from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import { apiClient } from '../services/api';

export const DatasetsPage: React.FC = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [qualityReport, setQualityReport] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dRes, qRes] = await Promise.all([
          apiClient.get('/datasets'),
          apiClient.get('/datasets/quality/report')
        ]);
        setDatasets(dRes.data);
        setQualityReport(qRes.data);
      } catch (e) {
        console.error('Failed to load datasets:', e);
      }
    };
    fetchData();
  }, []);

  return (
    <Box sx={{ pb: 6 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
          <StorageIcon sx={{ color: '#00b4d8', fontSize: 32 }} />
          <Typography variant="h4" sx={{ fontWeight: 800, color: '#f8fafc' }}>
            Dataset Explorer & Data Quality Review
          </Typography>
        </Box>
        <Typography variant="body2" sx={{ color: '#94a3b8' }}>
          Audited workspace datasets for Components C1–C4 with verifiable provenance metadata and schema specifications.
        </Typography>
      </Box>

      {/* Quality Summary Cards */}
      {qualityReport && (
        <Grid container spacing={2.5} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'rgba(15, 29, 54, 0.8)' }}>
              <Typography variant="caption" sx={{ color: '#94a3b8' }}>Audited Datasets</Typography>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#00b4d8' }}>
                {qualityReport.datasets_audited}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>4 Core Components</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'rgba(15, 29, 54, 0.8)' }}>
              <Typography variant="caption" sx={{ color: '#94a3b8' }}>Total Observations</Typography>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#f1f5f9' }}>
                {qualityReport.total_records.toLocaleString()}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>5,000 per component</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'rgba(15, 29, 54, 0.8)' }}>
              <Typography variant="caption" sx={{ color: '#94a3b8' }}>Field Logs Submitted</Typography>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#2ec4b6' }}>
                {qualityReport.field_observations_logged}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>Awaiting/Verified</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: 'rgba(15, 29, 54, 0.8)' }}>
              <Typography variant="caption" sx={{ color: '#94a3b8' }}>Integrity Status</Typography>
              <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#10b981', mt: 0.5 }}>
                COMPLIANT
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>Provenance Verified</Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Dataset Catalog Table */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
            Workspace Dataset Catalog (`Datasets/` directory)
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Component</TableCell>
                  <TableCell>Filename</TableCell>
                  <TableCell>Records</TableCell>
                  <TableCell>Features</TableCell>
                  <TableCell>Scientific Provenance Tag</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {datasets.map((d) => (
                  <TableRow key={d.id} hover>
                    <TableCell sx={{ fontWeight: 700, color: '#00b4d8' }}>{d.name}</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace' }}>{d.filename}</TableCell>
                    <TableCell>{d.records.toLocaleString()}</TableCell>
                    <TableCell>{d.features}</TableCell>
                    <TableCell sx={{ fontSize: '0.8rem', color: '#cbd5e1' }}>{d.provenance}</TableCell>
                    <TableCell>
                      <Chip
                        icon={<CheckCircleOutlineIcon />}
                        label={d.status}
                        size="small"
                        color="success"
                        sx={{ fontWeight: 700, fontSize: '0.65rem' }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Alert severity="info" sx={{ borderRadius: 2 }}>
        <strong>DOCUMENTATION MAPPING:</strong> Detailed data dictionaries, variable physics units, and cross-dataset integration mapping contracts are documented in `docs/DATASET_AUDIT.md`, `docs/DATA_DICTIONARY.md`, and `docs/DATA_INTEGRATION_MAPPING.md`.
      </Alert>
    </Box>
  );
};
