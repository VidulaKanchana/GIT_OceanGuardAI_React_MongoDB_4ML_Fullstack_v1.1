import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Box, Typography, Chip, Paper } from '@mui/material';
import L from 'leaflet';

// Fix leaflet icon default issues in bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface Port {
  id: string;
  name: string;
  lat: number;
  lon: number;
}

interface Zone {
  zone_id: string;
  latitude: number;
  longitude: number;
  habitat_suitability_index: number;
  distance_km?: number;
  sst_c?: number;
}

interface FishingMapProps {
  ports?: Port[];
  zones?: Zone[];
  selectedZone?: Zone | null;
  departurePortId?: string;
  height?: string;
}

const DEFAULT_PORTS: Port[] = [
  { id: 'P_GALLE', name: 'Galle Fishery Harbour', lat: 6.033, lon: 80.217 },
  { id: 'P_MIRISSA', name: 'Mirissa Fishery Harbour', lat: 5.945, lon: 80.455 },
  { id: 'P_TANGALLE', name: 'Tangalle Fishery Harbour', lat: 6.024, lon: 80.796 },
  { id: 'P_NEGOMBO', name: 'Negombo Fishery Harbour', lat: 7.208, lon: 79.835 },
  { id: 'P_PELIYAGODA', name: 'Peliyagoda Market Port', lat: 6.965, lon: 79.885 },
  { id: 'P_BERUWALA', name: 'Beruwala Harbour', lat: 6.478, lon: 79.982 },
  { id: 'P_TRINCOMALEE', name: 'Cod Bay Trincomalee', lat: 8.571, lon: 81.233 }
];

export const FishingMap: React.FC<FishingMapProps> = ({
  ports = DEFAULT_PORTS,
  zones = [],
  selectedZone = null,
  departurePortId = 'P_GALLE',
  height = '480px',
}) => {
  const selectedPort = ports.find((p) => p.id === departurePortId) || ports[0];

  // Great-circle reference route path
  const routePoints: [number, number][] = selectedZone
    ? [
        [selectedPort.lat, selectedPort.lon],
        [selectedZone.latitude, selectedZone.longitude],
      ]
    : [];

  const getHsiColor = (hsi: number) => {
    if (hsi >= 0.75) return '#10b981'; // High
    if (hsi >= 0.55) return '#00b4d8'; // Moderate
    return '#f59e0b'; // Low
  };

  return (
    <Box sx={{ position: 'relative', width: '100%', height, borderRadius: 3, overflow: 'hidden', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
      <MapContainer
        center={[6.5, 80.5]}
        zoom={8}
        style={{ width: '100%', height: '100%', background: '#0a192f' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Ports Markers */}
        {ports.map((port) => (
          <Marker key={port.id} position={[port.lat, port.lon]}>
            <Popup>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0f172a' }}>
                {port.name}
              </Typography>
              <Typography variant="caption" sx={{ color: '#475569' }}>
                Port Code: {port.id} | ({port.lat.toFixed(3)}, {port.lon.toFixed(3)})
              </Typography>
            </Popup>
          </Marker>
        ))}

        {/* Candidate Fishing Zones */}
        {zones.map((zone) => {
          const color = getHsiColor(zone.habitat_suitability_index);
          const isSelected = selectedZone?.zone_id === zone.zone_id;
          return (
            <CircleMarker
              key={zone.zone_id}
              center={[zone.latitude, zone.longitude]}
              radius={isSelected ? 10 : 7}
              pathOptions={{
                color: isSelected ? '#ffffff' : color,
                fillColor: color,
                fillOpacity: isSelected ? 0.9 : 0.65,
                weight: isSelected ? 3 : 1.5,
              }}
            >
              <Popup>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0f172a' }}>
                  Zone {zone.zone_id}
                </Typography>
                <Typography variant="body2" sx={{ color: '#334155' }}>
                  Habitat Suitability (HSI): <strong>{zone.habitat_suitability_index.toFixed(3)}</strong>
                </Typography>
                {zone.sst_c && (
                  <Typography variant="caption" display="block" sx={{ color: '#475569' }}>
                    SST: {zone.sst_c.toFixed(1)}°C
                  </Typography>
                )}
                {zone.distance_km && (
                  <Typography variant="caption" display="block" sx={{ color: '#475569' }}>
                    Distance from departure: {zone.distance_km.toFixed(1)} km
                  </Typography>
                )}
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Route reference polyline */}
        {routePoints.length === 2 && (
          <Polyline
            positions={routePoints}
            pathOptions={{
              color: '#00b4d8',
              weight: 3,
              dashArray: '8, 8',
              opacity: 0.85,
            }}
          />
        )}
      </MapContainer>

      {/* Map Legend Overlay */}
      <Paper
        sx={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          zIndex: 1000,
          p: 1.5,
          backgroundColor: 'rgba(15, 29, 54, 0.92)',
          backdropFilter: 'blur(8px)',
          borderRadius: 2,
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Typography variant="caption" sx={{ fontWeight: 700, color: '#94a3b8', display: 'block', mb: 0.5 }}>
          SPATIAL HSI SUITABILITY
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Chip size="small" label="High HSI ≥0.75" sx={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#34d399', fontSize: '0.65rem' }} />
          <Chip size="small" label="Medium ≥0.55" sx={{ backgroundColor: 'rgba(0, 180, 216, 0.2)', color: '#38bdf8', fontSize: '0.65rem' }} />
          <Chip size="small" label="Low <0.55" sx={{ backgroundColor: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', fontSize: '0.65rem' }} />
        </Box>
        <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.6rem', display: 'block', mt: 0.8 }}>
          Reference path: Great-Circle line (Non-navigational).
        </Typography>
      </Paper>
    </Box>
  );
};
