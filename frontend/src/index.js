import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import './i18n'; // initialise react-i18next avant le montage de l'app (sinon labels = clés)
import App from './App';

const root = createRoot(document.getElementById('root'));
root.render(<App />);
