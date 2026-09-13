import { createRoot } from 'react-dom/client';

import './index.css';
import './i18n';
import App from './App';

// Point d'entrée mince : l'application complète vit dans App.js, qui monte
// déjà AuthProvider, les onze modules et le thème. L'index.js précédent
// recréait un App() local et rendait cinq de ces modules en placeholder —
// App.js n'était alors importé par personne.
createRoot(document.getElementById('root')).render(<App />);
