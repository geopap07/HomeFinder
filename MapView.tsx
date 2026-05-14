import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Property, formatPrice } from '@/data/properties';
import { Link } from 'react-router-dom';
import 'leaflet/dist/leaflet.css';

// Fix default marker icon
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const priceIcon = (price: number) =>
  L.divIcon({
    className: 'custom-marker',
    html: `<div style="background:hsl(216,85%,48%);color:white;padding:4px 8px;border-radius:8px;font-size:12px;font-weight:600;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,0.2);transform:translateX(-50%)">${formatPrice(price)}</div>`,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
  });

interface MapViewProps {
  properties: Property[];
  selectedId?: string;
}

const FitBounds = ({ properties }: { properties: Property[] }) => {
  const map = useMap();
  useEffect(() => {
    if (properties.length === 0) return;
    const bounds = L.latLngBounds(properties.map(p => [p.lat, p.lng]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
  }, [properties, map]);
  return null;
};

const MapView = ({ properties, selectedId }: MapViewProps) => {
  if (properties.length === 0) {
    return (
      <div className="flex h-full items-center justify-center rounded-xl bg-secondary text-muted-foreground">
        No properties to display on map
      </div>
    );
  }

  const center: [number, number] = [properties[0].lat, properties[0].lng];

  return (
    <MapContainer center={center} zoom={11} className="h-full w-full rounded-xl" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/">OSM</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds properties={properties} />
      {properties.map(p => (
        <Marker key={p.id} position={[p.lat, p.lng]} icon={priceIcon(p.price)}>
          <Popup>
            <Link to={`/property/${p.id}`} className="block max-w-[200px]">
              <img src={p.images[0]} alt={p.title} className="mb-2 h-24 w-full rounded object-cover" />
              <p className="text-sm font-semibold">{p.title}</p>
              <p className="text-xs text-muted-foreground">{formatPrice(p.price)}</p>
            </Link>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

export default MapView;
