import React, { useCallback, useEffect, useState } from 'react';
import { csrfFetch } from '../../services/csrf';

// Rédacteur en chef (décision de l'exploitant du 07/11/2026) : aucune
// dépêche collectée n'est affichée sans validation. Panneau visible du seul
// compte admin ; le serveur refuse de toute façon toute autre session.

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api/news`;

const ONGLETS = [
  ['a_valider', 'À valider'],
  ['publies', 'Publiés'],
  ['masques', 'Masqués'],
  ['ecartes', 'Écartés'],
  ['regles', 'Blocages'],
  ['ajouter', 'Ajouter un article'],
];

const bouton = {
  background: 'var(--overlay)',
  border: '1px solid var(--overlay-border)',
  color: 'var(--text)',
};

function messageErreur(corps, statut) {
  const detail = corps?.detail;
  if (detail?.message) return detail.message;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return 'Champ invalide : vérifiez le formulaire.';
  return `Erreur ${statut}`;
}

async function appeler(chemin, methode = 'POST', corps) {
  const reponse = await csrfFetch(`${API}${chemin}`, {
    method: methode,
    headers: corps ? { 'Content-Type': 'application/json' } : undefined,
    body: corps ? JSON.stringify(corps) : undefined,
  });
  const donnees = await reponse.json().catch(() => ({}));
  if (!reponse.ok) throw new Error(messageErreur(donnees, reponse.status));
  return donnees;
}

const Action = ({ children, onClick, disabled, titre }) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    title={titre}
    className="px-2 py-1 rounded-md text-xs font-medium disabled:opacity-50"
    style={bouton}
  >
    {children}
  </button>
);

const Ligne = ({ article, onglet, occupe, agir, epingles, version }) => {
  const rang = epingles.indexOf(article.id);
  return (
    <li
      className="flex gap-3 rounded-lg border p-3"
      style={{ borderColor: 'var(--overlay-border)', background: 'var(--lift)' }}
    >
      {article.has_image ? (
        <img
          src={`${API}/images/${encodeURIComponent(article.id)}?v=${version}`}
          alt=""
          className="w-28 h-20 shrink-0 rounded-md object-cover"
        />
      ) : (
        <div
          className="w-28 h-20 shrink-0 rounded-md flex items-center justify-center text-[10px] text-center text-[var(--afcfta-muted)]"
          style={{ border: '1px dashed var(--overlay-border)' }}
        >
          sans image
        </div>
      )}
      <div className="min-w-0 flex-1 space-y-1">
        <a
          href={article.link}
          target="_blank"
          rel="noopener noreferrer"
          className="block font-medium text-sm text-[var(--text)] hover:underline"
        >
          {article.pinned ? '★ ' : ''}
          {article.title}
        </a>
        <p className="text-xs text-[var(--afcfta-muted)] line-clamp-2">{article.summary}</p>
        <p className="text-[11px] text-[var(--afcfta-muted)]">
          {article.source}
          {article.manuel ? ' · ajouté à la main' : ''}
          {article.bloque ? ' · masqué par un blocage' : ''}
        </p>
        <div className="flex flex-wrap gap-1.5 pt-1">
          {onglet === 'a_valider' && (
            <>
              <Action disabled={occupe} onClick={() => agir('decision', { id: article.id, action: 'publier' })}>
                Publier
              </Action>
              <Action disabled={occupe} onClick={() => agir('epingle', { id: article.id })}>
                Publier à la une
              </Action>
              <Action disabled={occupe} onClick={() => agir('decision', { id: article.id, action: 'ecarter' })}>
                Écarter
              </Action>
            </>
          )}
          {onglet === 'publies' && (
            <>
              {article.pinned ? (
                <>
                  <Action
                    disabled={occupe || rang <= 0}
                    titre="Monter"
                    onClick={() => agir('monter', { id: article.id })}
                  >
                    ↑
                  </Action>
                  <Action
                    disabled={occupe || rang === epingles.length - 1}
                    titre="Descendre"
                    onClick={() => agir('descendre', { id: article.id })}
                  >
                    ↓
                  </Action>
                  <Action disabled={occupe} onClick={() => agir('epingle', { id: article.id, epingler: false })}>
                    Retirer de la une
                  </Action>
                </>
              ) : (
                <Action disabled={occupe} onClick={() => agir('epingle', { id: article.id })}>
                  À la une (7 jours)
                </Action>
              )}
              <Action disabled={occupe} onClick={() => agir('decision', { id: article.id, action: 'masquer' })}>
                Masquer
              </Action>
            </>
          )}
          {(onglet === 'masques' || onglet === 'ecartes') && (
            <Action disabled={occupe} onClick={() => agir('decision', { id: article.id, action: 'retablir' })}>
              Rétablir
            </Action>
          )}
          {(onglet === 'a_valider' || onglet === 'publies') && (
            <>
              <Action disabled={occupe} onClick={() => agir('image', { id: article.id })}>
                {article.has_image ? 'Rechercher à nouveau l’image' : 'Chercher l’image'}
              </Action>
              <Action disabled={occupe} onClick={() => agir('autre-image', { id: article.id })}>
                Autre image (lien)
              </Action>
              {article.has_image && (
                <Action disabled={occupe} onClick={() => agir('retirer-image', { id: article.id })}>
                  Retirer l’image
                </Action>
              )}
            </>
          )}
        </div>
      </div>
    </li>
  );
};

const champ = 'w-full rounded-md px-2 py-1.5 text-sm';
const styleChamp = { background: 'var(--overlay)', border: '1px solid var(--overlay-border)', color: 'var(--text)' };

const FormulaireArticle = ({ occupe, envoyer }) => {
  const vide = { title: '', summary: '', link: '', source: '', image: '' };
  const [valeurs, setValeurs] = useState(vide);
  const changer = (cle) => (e) => setValeurs({ ...valeurs, [cle]: e.target.value });
  const soumettre = async (e) => {
    e.preventDefault();
    const corps = { ...valeurs };
    if (!corps.image) delete corps.image;
    if (await envoyer(corps)) setValeurs(vide);
  };
  return (
    <form onSubmit={soumettre} className="grid gap-2 max-w-2xl">
      <input className={champ} style={styleChamp} placeholder="Titre" required minLength={3} maxLength={300} value={valeurs.title} onChange={changer('title')} />
      <textarea className={champ} style={styleChamp} placeholder="Résumé (4 à 5 lignes)" maxLength={1000} rows={4} value={valeurs.summary} onChange={changer('summary')} />
      <input className={champ} style={styleChamp} placeholder="Lien de l’article (https://…)" type="url" required value={valeurs.link} onChange={changer('link')} />
      <input className={champ} style={styleChamp} placeholder="Source (ex. APS)" required minLength={2} maxLength={100} value={valeurs.source} onChange={changer('source')} />
      <input className={champ} style={styleChamp} placeholder="Lien d’une image (facultatif)" type="url" value={valeurs.image} onChange={changer('image')} />
      <div>
        <Action disabled={occupe} onClick={soumettre}>Publier l’article</Action>
      </div>
    </form>
  );
};

const Blocages = ({ regles, occupe, agir }) => {
  const [type, setType] = useState('source');
  const [valeur, setValeur] = useState('');
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-center">
        <select className="rounded-md px-2 py-1.5 text-sm" style={styleChamp} value={type} onChange={(e) => setType(e.target.value)}>
          <option value="source">Source</option>
          <option value="mot">Mot ou expression</option>
        </select>
        <input className="rounded-md px-2 py-1.5 text-sm" style={styleChamp} placeholder={type === 'source' ? 'Nom exact de la source' : 'Mot entier'} minLength={2} maxLength={100} value={valeur} onChange={(e) => setValeur(e.target.value)} />
        <Action
          disabled={occupe || valeur.trim().length < 2}
          onClick={async () => {
            if (await agir('bloquer', { type, valeur: valeur.trim() })) setValeur('');
          }}
        >
          Bloquer
        </Action>
      </div>
      {regles.length === 0 ? (
        <p className="text-sm text-[var(--afcfta-muted)]">Aucun blocage.</p>
      ) : (
        <ul className="space-y-1">
          {regles.map((r) => (
            <li key={r.id} className="flex items-center gap-2 text-sm text-[var(--text)]">
              <span>{r.type === 'source' ? 'Source' : 'Mot'} : {r.valeur}</span>
              <Action disabled={occupe} onClick={() => agir('debloquer', { id: r.id })}>Débloquer</Action>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

const NewsRedaction = ({ onChange }) => {
  const [etat, setEtat] = useState(null);
  const [onglet, setOnglet] = useState('a_valider');
  const [occupe, setOccupe] = useState(false);
  const [message, setMessage] = useState(null);
  const [version, setVersion] = useState(0);

  const charger = useCallback(async () => {
    try {
      const reponse = await fetch(API + '/redaction', { credentials: 'include' });
      const donnees = await reponse.json().catch(() => ({}));
      if (!reponse.ok) throw new Error(messageErreur(donnees, reponse.status));
      setEtat(donnees);
    } catch (e) {
      setMessage({ erreur: true, texte: e.message });
    }
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  const epingles = (etat?.publies || []).filter((a) => a.pinned).map((a) => a.id);

  const agir = async (quoi, donnees) => {
    setOccupe(true);
    setMessage(null);
    try {
      if (quoi === 'decision') await appeler('/redaction/decision', 'POST', donnees);
      else if (quoi === 'epingle') await appeler('/redaction/epingle', 'POST', donnees);
      else if (quoi === 'monter' || quoi === 'descendre') {
        const ordre = [...epingles];
        const i = ordre.indexOf(donnees.id);
        const j = quoi === 'monter' ? i - 1 : i + 1;
        [ordre[i], ordre[j]] = [ordre[j], ordre[i]];
        await appeler('/redaction/une', 'POST', { ids: ordre });
      } else if (quoi === 'image') await appeler('/redaction/image', 'POST', donnees);
      else if (quoi === 'autre-image') {
        const url = window.prompt('Lien de l’image (https://…) :');
        if (!url) return false;
        await appeler('/redaction/image', 'POST', { id: donnees.id, url });
      } else if (quoi === 'retirer-image') await appeler('/redaction/image/retirer', 'POST', donnees);
      else if (quoi === 'tout') {
        const r = await appeler('/redaction/publier-tout');
        setMessage({ texte: `${r.publies} article(s) publié(s).` });
      } else if (quoi === 'bloquer') await appeler('/redaction/regles', 'POST', donnees);
      else if (quoi === 'debloquer') await appeler(`/redaction/regles/${encodeURIComponent(donnees.id)}`, 'DELETE');
      else if (quoi === 'manuel') {
        const r = await appeler('/redaction/manuel', 'POST', donnees);
        setMessage(
          r.image_refusee
            ? { erreur: true, texte: `Article publié, image refusée : ${r.image_refusee}` }
            : { texte: 'Article publié.' }
        );
      }
      setVersion((v) => v + 1);
      await charger();
      onChange?.();
      return true;
    } catch (e) {
      setMessage({ erreur: true, texte: e.message });
      return false;
    } finally {
      setOccupe(false);
    }
  };

  const liste = etat && onglet !== 'regles' && onglet !== 'ajouter' ? etat[onglet] || [] : [];

  return (
    <section
      data-testid="redaction"
      className="rounded-2xl border p-4 md:p-5 space-y-4"
      style={{ background: 'var(--panel)', borderColor: 'color-mix(in srgb, var(--gold) 40%, transparent)' }}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-bold text-[var(--text)]">Rédaction — visible par vous seul</h3>
        {onglet === 'a_valider' && (etat?.a_valider?.length || 0) > 0 && (
          <Action disabled={occupe} onClick={() => agir('tout')}>
            Tout publier ({etat.a_valider.length})
          </Action>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5" role="tablist">
        {ONGLETS.map(([cle, libelle]) => {
          const nombre = Array.isArray(etat?.[cle]) ? ` (${etat[cle].length})` : '';
          return (
            <button
              key={cle}
              type="button"
              role="tab"
              aria-selected={onglet === cle}
              onClick={() => setOnglet(cle)}
              className="px-3 py-1.5 rounded-full text-xs font-semibold"
              style={{
                ...bouton,
                ...(onglet === cle ? { background: 'color-mix(in srgb, var(--gold) 22%, transparent)' } : {}),
              }}
            >
              {libelle}
              {cle !== 'ajouter' && cle !== 'regles' ? nombre : ''}
            </button>
          );
        })}
      </div>

      {message && (
        <p role="status" className="text-sm" style={{ color: message.erreur ? 'var(--danger)' : 'var(--text)' }}>
          {message.texte}
        </p>
      )}

      {!etat ? (
        <p className="text-sm text-[var(--afcfta-muted)]">Chargement…</p>
      ) : onglet === 'ajouter' ? (
        <FormulaireArticle occupe={occupe} envoyer={(corps) => agir('manuel', corps)} />
      ) : onglet === 'regles' ? (
        <Blocages regles={etat.regles || []} occupe={occupe} agir={agir} />
      ) : liste.length === 0 ? (
        <p className="text-sm text-[var(--afcfta-muted)]">Rien ici pour le moment.</p>
      ) : (
        <ul className="space-y-2 max-h-[36rem] overflow-y-auto pr-1">
          {liste.map((article) => (
            <Ligne
              key={article.id}
              article={article}
              onglet={onglet}
              occupe={occupe}
              agir={agir}
              epingles={epingles}
              version={version}
            />
          ))}
        </ul>
      )}
    </section>
  );
};

export default NewsRedaction;
