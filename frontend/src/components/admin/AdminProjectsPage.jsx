import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { toast } from '../../hooks/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const ALL_ISO3 = [
  'DZA','AGO','BEN','BWA','BFA','BDI','CMR','CPV','CAF','TCD','COM','COG','COD','CIV',
  'DJI','EGY','GNQ','ERI','SWZ','ETH','GAB','GMB','GHA','GIN','GNB','KEN','LSO','LBR',
  'LBY','MDG','MWI','MLI','MRT','MUS','MAR','MOZ','NAM','NER','NGA','RWA','STP','SEN',
  'SYC','SLE','SOM','ZAF','SSD','SDN','TZA','TGO','TUN','UGA','ZMB','ZWE'
];

const COUNTRY_NAMES = {
  DZA:'Algérie',AGO:'Angola',BEN:'Bénin',BWA:'Botswana',BFA:'Burkina Faso',BDI:'Burundi',
  CMR:'Cameroun',CPV:'Cap-Vert',CAF:'Centrafrique',TCD:'Tchad',COM:'Comores',COG:'Congo',
  COD:'RDC',CIV:"Côte d'Ivoire",DJI:'Djibouti',EGY:'Égypte',GNQ:'Guinée Équatoriale',
  ERI:'Érythrée',SWZ:'Eswatini',ETH:'Éthiopie',GAB:'Gabon',GMB:'Gambie',GHA:'Ghana',
  GIN:'Guinée',GNB:'Guinée-Bissau',KEN:'Kenya',LSO:'Lesotho',LBR:'Libéria',LBY:'Libye',
  MDG:'Madagascar',MWI:'Malawi',MLI:'Mali',MRT:'Mauritanie',MUS:'Maurice',MAR:'Maroc',
  MOZ:'Mozambique',NAM:'Namibie',NER:'Niger',NGA:'Nigeria',RWA:'Rwanda',STP:'São Tomé',
  SEN:'Sénégal',SYC:'Seychelles',SLE:'Sierra Leone',SOM:'Somalie',ZAF:'Afrique du Sud',
  SSD:'Soudan du Sud',SDN:'Soudan',TZA:'Tanzanie',TGO:'Togo',TUN:'Tunisie',UGA:'Ouganda',
  ZMB:'Zambie',ZWE:'Zimbabwe'
};

const EMPTY_PROJECT = {
  titre: '', secteur: '', statut: '', budget: '', echeance: '',
  description: '', impact: '', partenaires: '', source: '',
};

export default function AdminProjectsPage() {
  const [adminKey, setAdminKey] = useState(() => localStorage.getItem('zlecaf_admin_key') || '');
  const [keyInput, setKeyInput] = useState('');
  const [authed, setAuthed] = useState(false);
  const [countries, setCountries] = useState([]);
  const [selected, setSelected] = useState('DZA');
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingIdx, setEditingIdx] = useState(null); // null = none, -1 = new, otherwise index
  const [form, setForm] = useState({ ...EMPTY_PROJECT });

  const adminAxios = useMemo(() => axios.create({
    baseURL: API,
    headers: adminKey ? { 'X-API-Key': adminKey } : {},
  }), [adminKey]);

  // Verify key on load / change
  useEffect(() => {
    if (!adminKey) { setAuthed(false); return; }
    setLoading(true);
    adminAxios.get('/admin/projects/countries')
      .then((r) => { setCountries(r.data || []); setAuthed(true); })
      .catch(() => { setAuthed(false); toast({ title: 'Clé admin invalide', variant: 'destructive' }); })
      .finally(() => setLoading(false));
  }, [adminKey, adminAxios]);

  // Load projects when country selected
  useEffect(() => {
    if (!authed || !selected) return;
    setLoading(true);
    adminAxios.get(`/admin/projects/${selected}`)
      .then((r) => setProjects(r.data || []))
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  }, [authed, selected, adminAxios]);

  const refreshCountries = () => {
    adminAxios.get('/admin/projects/countries').then((r) => setCountries(r.data || []));
  };

  const handleLogin = () => {
    if (!keyInput.trim()) return;
    localStorage.setItem('zlecaf_admin_key', keyInput.trim());
    setAdminKey(keyInput.trim());
  };

  const handleLogout = () => {
    localStorage.removeItem('zlecaf_admin_key');
    setAdminKey('');
    setAuthed(false);
    setCountries([]);
    setProjects([]);
  };

  const startEdit = (idx) => {
    setEditingIdx(idx);
    setForm(idx === -1 ? { ...EMPTY_PROJECT } : { ...projects[idx] });
  };

  const cancelEdit = () => {
    setEditingIdx(null);
    setForm({ ...EMPTY_PROJECT });
  };

  const saveProject = async () => {
    if (!form.titre.trim() || form.titre.trim().length < 2) {
      toast({ title: 'Titre requis (min 2 caractères)', variant: 'destructive' });
      return;
    }
    setLoading(true);
    try {
      if (editingIdx === -1) {
        const r = await adminAxios.post(`/admin/projects/${selected}`, form);
        setProjects(r.data);
        toast({ title: 'Projet ajouté' });
      } else {
        const r = await adminAxios.put(`/admin/projects/${selected}/${editingIdx}`, form);
        setProjects(r.data);
        toast({ title: 'Projet mis à jour' });
      }
      cancelEdit();
      refreshCountries();
    } catch (e) {
      toast({ title: 'Erreur lors de la sauvegarde', description: e?.response?.data?.detail || e.message, variant: 'destructive' });
    } finally { setLoading(false); }
  };

  const deleteProject = async (idx) => {
    // eslint-disable-next-line no-alert
    if (!window.confirm('Supprimer ce projet ?')) return;
    setLoading(true);
    try {
      const r = await adminAxios.delete(`/admin/projects/${selected}/${idx}`);
      setProjects(r.data);
      toast({ title: 'Projet supprimé' });
      refreshCountries();
    } catch (e) {
      toast({ title: 'Erreur', description: e?.response?.data?.detail || e.message, variant: 'destructive' });
    } finally { setLoading(false); }
  };

  if (!authed) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-zinc-950 text-zinc-100">
        <Card className="w-full max-w-md bg-zinc-900 border-zinc-800" data-testid="admin-login-card">
          <CardHeader>
            <CardTitle>Admin — Projets Structurants</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-zinc-400">Saisissez votre clé admin (X-API-Key tier <code>admin</code>).</p>
            <Input
              type="password"
              placeholder="zlecaf-admin-key"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              data-testid="admin-key-input"
            />
            <Button onClick={handleLogin} className="w-full" data-testid="admin-login-btn">Se connecter</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const editing = editingIdx !== null;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6" data-testid="admin-projects-page">
      <div className="max-w-7xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Admin — Projets Structurants & Perspectives 2030</h1>
          <Button variant="outline" onClick={handleLogout} data-testid="admin-logout-btn">Déconnexion</Button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm text-zinc-400">Pays :</label>
          <select
            className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2"
            value={selected}
            onChange={(e) => { setSelected(e.target.value); cancelEdit(); }}
            data-testid="admin-country-select"
          >
            {ALL_ISO3.map((iso) => {
              const c = countries.find((x) => x.iso3 === iso);
              const count = c ? c.project_count : 0;
              return (
                <option key={iso} value={iso}>
                  {iso} — {COUNTRY_NAMES[iso] || iso} ({count} projet{count > 1 ? 's' : ''})
                </option>
              );
            })}
          </select>
          <Button onClick={() => startEdit(-1)} disabled={editing} data-testid="admin-add-project-btn">
            + Ajouter un projet
          </Button>
          {loading && <span className="text-sm text-zinc-400">Chargement…</span>}
        </div>

        {editing && (
          <Card className="bg-zinc-900 border-emerald-700" data-testid="admin-project-form">
            <CardHeader>
              <CardTitle>{editingIdx === -1 ? 'Nouveau projet' : `Édition projet #${editingIdx + 1}`}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                ['titre','Titre *'],['secteur','Secteur'],['statut','Statut'],
                ['budget','Budget'],['echeance','Échéance'],['partenaires','Partenaires'],
                ['source','Source'],
              ].map(([k,label]) => (
                <div key={k}>
                  <label className="text-xs text-zinc-400">{label}</label>
                  <Input
                    value={form[k] || ''}
                    onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                    data-testid={`admin-field-${k}`}
                  />
                </div>
              ))}
              <div>
                <label className="text-xs text-zinc-400">Description</label>
                <Textarea
                  rows={3}
                  value={form.description || ''}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  data-testid="admin-field-description"
                />
              </div>
              <div>
                <label className="text-xs text-zinc-400">Impact</label>
                <Textarea
                  rows={3}
                  value={form.impact || ''}
                  onChange={(e) => setForm({ ...form, impact: e.target.value })}
                  data-testid="admin-field-impact"
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={saveProject} disabled={loading} data-testid="admin-save-btn">Enregistrer</Button>
                <Button variant="outline" onClick={cancelEdit} disabled={loading} data-testid="admin-cancel-btn">Annuler</Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {projects.length === 0 && !loading && (
            <p className="text-zinc-500 italic col-span-full">Aucun projet pour ce pays.</p>
          )}
          {projects.map((p, idx) => (
            <Card key={idx} className="bg-zinc-900 border-zinc-800" data-testid={`admin-project-card-${idx}`}>
              <CardHeader>
                <CardTitle className="text-base">{p.titre}</CardTitle>
                <div className="flex flex-wrap gap-2 mt-1">
                  {p.secteur && <Badge variant="outline">{p.secteur}</Badge>}
                  {p.echeance && <Badge variant="outline">{p.echeance}</Badge>}
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {p.statut && <p><strong>Statut :</strong> {p.statut}</p>}
                {p.budget && <p><strong>Budget :</strong> {p.budget}</p>}
                {p.description && <p className="text-zinc-300">{p.description}</p>}
                {p.impact && <p className="text-zinc-400"><strong>Impact :</strong> {p.impact}</p>}
                {p.partenaires && <p className="text-zinc-400"><strong>Partenaires :</strong> {p.partenaires}</p>}
                {p.source && <p className="text-xs text-zinc-500 italic">Source : {p.source}</p>}
                <div className="flex gap-2 pt-2">
                  <Button size="sm" onClick={() => startEdit(idx)} data-testid={`admin-edit-${idx}`}>Modifier</Button>
                  <Button size="sm" variant="destructive" onClick={() => deleteProject(idx)} data-testid={`admin-delete-${idx}`}>Supprimer</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
