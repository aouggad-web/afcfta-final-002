/**
 * use-toast — notification toast autonome.
 *
 * Le code applicatif n'importe que `toast({ title, description, variant })`
 * et aucun composant <Toaster/> n'est monté. Cette implémentation légère rend
 * donc elle-même une notification éphémère dans document.body puis la retire,
 * sans dépendre d'un provider. Sûre côté SSR/tests : no-op si `document` est
 * absent.
 */

const CONTAINER_ID = 'app-toast-container';

function ensureContainer() {
  if (typeof document === 'undefined') return null;
  let container = document.getElementById(CONTAINER_ID);
  if (!container) {
    container = document.createElement('div');
    container.id = CONTAINER_ID;
    container.style.cssText = [
      'position:fixed',
      'top:16px',
      'right:16px',
      'z-index:9999',
      'display:flex',
      'flex-direction:column',
      'gap:8px',
      'max-width:360px',
      'pointer-events:none',
    ].join(';');
    document.body.appendChild(container);
  }
  return container;
}

export function toast({ title, description, variant = 'default', duration = 4000 } = {}) {
  const container = ensureContainer();
  if (!container) return { dismiss: () => {} };

  const el = document.createElement('div');
  const isDestructive = variant === 'destructive';
  el.style.cssText = [
    'pointer-events:auto',
    'padding:12px 14px',
    'border-radius:8px',
    'box-shadow:0 4px 14px rgba(0,0,0,0.15)',
    'font-size:0.9em',
    'line-height:1.35',
    `background:${isDestructive ? '#fdecea' : '#f0f7ff'}`,
    `border:1px solid ${isDestructive ? '#f5c6cb' : '#c9def5'}`,
    `color:${isDestructive ? '#721c24' : '#0b3d66'}`,
    'opacity:0',
    'transform:translateY(-6px)',
    'transition:opacity .18s ease, transform .18s ease',
  ].join(';');

  if (title) {
    const t = document.createElement('div');
    t.style.fontWeight = '600';
    t.textContent = title;
    el.appendChild(t);
  }
  if (description) {
    const d = document.createElement('div');
    d.textContent = description;
    el.appendChild(d);
  }

  container.appendChild(el);
  requestAnimationFrame(() => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  });

  const remove = () => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(-6px)';
    setTimeout(() => el.remove(), 200);
  };
  const timer = setTimeout(remove, duration);

  return {
    dismiss: () => {
      clearTimeout(timer);
      remove();
    },
  };
}

export function useToast() {
  return { toast };
}

export default useToast;
