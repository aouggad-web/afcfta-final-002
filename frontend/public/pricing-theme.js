// Thème de la page des tarifs, appliqué avant l'affichage (chargé de façon
// synchrone dans <head>). Fichier séparé : la CSP de la page n'autorise aucun
// script inline (audit INFO-3).
// Même thème que l'application (clair / sombre), avant l'affichage.
try { if (localStorage.getItem('zlecaf_theme') === 'light') document.documentElement.classList.add('theme-light'); } catch (e) {}
