import React, { useState } from 'react';
import ISIC4DetailTable from './ISIC4DetailTable';
import './styles.css';

export default function Production() {
  const [selectedCountry, setSelectedCountry] = useState('ETH');

  const countries = ['DZA', 'EGY', 'ETH', 'GHA', 'KEN', 'MAR', 'NGA', 'ZAF', 'TUN'];

  return (
    <div className="production-module">
      <div className="production-header">
        <h1>🏭 Production Africaine</h1>
        <p>Secteurs manufacturiers (UNIDO ISIC Rev.4) et capacités de production réelles</p>
      </div>

      <div className="production-controls">
        <label htmlFor="country-select">Sélectionner un pays :</label>
        <select
          id="country-select"
          value={selectedCountry}
          onChange={(e) => setSelectedCountry(e.target.value)}
          className="country-select"
        >
          {countries.map((iso3) => (
            <option key={iso3} value={iso3}>
              {iso3}
            </option>
          ))}
        </select>
      </div>

      <div className="production-content">
        <ISIC4DetailTable countryISO3={selectedCountry} />
      </div>
    </div>
  );
}
