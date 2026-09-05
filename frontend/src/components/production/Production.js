import React, { useState, useEffect } from 'react';
import ISIC4DetailTable from './ISIC4DetailTable';
import './styles.css';

const getBackendUrl = () => {
  const viteUrl = import.meta.env.VITE_BACKEND_URL;
  if (viteUrl) return viteUrl;
  return '';
};

export default function Production() {
  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCountries = async () => {
      try {
        setLoading(true);
        const backendUrl = getBackendUrl();
        const response = await fetch(`${backendUrl}/api/production/isic4/countries`);
        if (!response.ok) throw new Error(`Erreur: ${response.status}`);
        const data = await response.json();
        setCountries(data.countries || []);
        if (data.countries && data.countries.length > 0) {
          setSelectedCountry(data.countries[0]);
        }
        setError(null);
      } catch (err) {
        setError(err.message);
        setCountries([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCountries();
  }, []);

  return (
    <div className="production-module">
      <div className="production-header">
        <h1>🏭 Production Africaine</h1>
        <p>Secteurs manufacturiers (UNIDO ISIC Rev.4) et capacités de production réelles</p>
      </div>

      <div className="production-controls">
        <label htmlFor="country-select">Sélectionner un pays :</label>
        {loading && <span className="country-loading">Chargement des pays...</span>}
        {error && <span className="country-error">Erreur: {error}</span>}
        {!loading && countries.length > 0 && (
          <select
            id="country-select"
            value={selectedCountry || ''}
            onChange={(e) => setSelectedCountry(e.target.value)}
            className="country-select"
          >
            {countries.map((iso3) => (
              <option key={iso3} value={iso3}>
                {iso3}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="production-content">
        {selectedCountry && <ISIC4DetailTable countryISO3={selectedCountry} />}
      </div>
    </div>
  );
}
