import { createRoot } from 'react-dom/client';

import './index.css';
import './i18n';
// Installe l'intercepteur CSRF sur l'instance axios par défaut AVANT toute
// requête. Sans cet import, aucun module monté ne chargeait `services/csrf` —
// seuls des composants orphelins l'importaient — et chaque POST partait sans
// en-tête X-CSRF-Token : le serveur répondait 403 « CSRF token missing », à
// commencer par le calcul de la Tunisie, qui passe d'abord par POST /calcul.
import './services/csrf';
import App from './App';

// Point d'entrée mince : l'application complète vit dans App.js, qui monte
// déjà AuthProvider, les onze modules et le thème. L'index.js précédent
// recréait un App() local et rendait cinq de ces modules en placeholder —
// App.js n'était alors importé par personne.
createRoot(document.getElementById('root')).render(<App />);
