import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { useAuth, formatApiErrorDetail } from '../../context/AuthContext';
import { toast } from '../../hooks/use-toast';

export default function AuthModal({ open, onClose, onAuthenticated, language = 'fr' }) {
  const {
    user,
    login,
    register,
    logout,
    supabaseEnabled,
    recovery,
    requestPasswordReset,
    updatePassword,
    exportAccount,
    deleteAccount,
  } = useAuth();
  const isFr = language === 'fr';
  const [tab, setTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  });
  // Écrans hors onglets : 'confirm' (email de confirmation envoyé),
  // 'forgot' / 'forgotSent' (mot de passe oublié), 'confirmDelete'.
  const [view, setView] = useState(null);
  const [forgotEmail, setForgotEmail] = useState('');
  const [newPassword, setNewPassword] = useState({ password: '', confirm: '' });

  const resetForms = () => {
    setTab('login');
    setLoginForm({ email: '', password: '' });
    setRegisterForm({ name: '', email: '', password: '', confirmPassword: '', acceptTerms: false });
    setErrorMessage('');
    setView(null);
    setForgotEmail('');
    setNewPassword({ password: '', confirm: '' });
  };

  const handleClose = () => {
    resetForms();
    onClose();
  };

  const handleAuthenticated = () => {
    resetForms();
    if (onAuthenticated) {
      onAuthenticated();
    } else {
      onClose();
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setLoading(true);
    try {
      await login(loginForm.email.trim().toLowerCase(), loginForm.password);
      toast({ title: isFr ? 'Connecté' : 'Logged in', description: isFr ? 'Bienvenue !' : 'Welcome back!' });
      handleAuthenticated();
    } catch (err) {
      const description = formatApiErrorDetail(
        err.response?.data?.detail,
        isFr ? 'Connexion impossible. Vérifiez votre accès réseau et réessayez.' : 'Unable to sign in. Check your connection and try again.'
      );
      setErrorMessage(description);
      toast({
        title: isFr ? 'Erreur de connexion' : 'Login error',
        description,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    const name = registerForm.name.trim().replace(/\s+/g, ' ');
    const email = registerForm.email.trim().toLowerCase();
    if (!name) {
      setErrorMessage(isFr ? 'Veuillez indiquer votre nom.' : 'Please enter your name.');
      return;
    }
    if (registerForm.password !== registerForm.confirmPassword) {
      setErrorMessage(isFr ? 'Les mots de passe ne correspondent pas.' : 'Passwords do not match.');
      return;
    }
    if (!registerForm.acceptTerms) {
      setErrorMessage(
        isFr
          ? 'Veuillez accepter les conditions d\'utilisation et la politique de confidentialité.'
          : 'Please accept the terms of use and the privacy policy.'
      );
      return;
    }

    setLoading(true);
    try {
      const result = await register(name, email, registerForm.password);
      if (result?.needsConfirmation) {
        setView('confirm');
        return;
      }
      toast({
        title: isFr ? 'Compte créé' : 'Account created',
        description: isFr ? 'Bienvenue sur ZLECAf Intelligence !' : 'Welcome to ZLECAf Intelligence!',
      });
      handleAuthenticated();
    } catch (err) {
      const description = formatApiErrorDetail(
        err.response?.data?.detail,
        isFr ? 'Inscription impossible. Vérifiez votre accès réseau et réessayez.' : 'Unable to register. Check your connection and try again.'
      );
      setErrorMessage(description);
      toast({
        title: isFr ? 'Erreur d\'inscription' : 'Registration error',
        description,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const runAction = async (action, fallbackFr, fallbackEn) => {
    setErrorMessage('');
    setLoading(true);
    try {
      await action();
    } catch (err) {
      setErrorMessage(formatApiErrorDetail(err.response?.data?.detail, isFr ? fallbackFr : fallbackEn));
    } finally {
      setLoading(false);
    }
  };

  const handleForgot = (e) => {
    e.preventDefault();
    runAction(
      async () => {
        await requestPasswordReset(forgotEmail);
        setView('forgotSent');
      },
      'Envoi impossible. Réessayez dans quelques minutes.',
      'Unable to send. Try again in a few minutes.'
    );
  };

  const handleNewPassword = (e) => {
    e.preventDefault();
    if (newPassword.password !== newPassword.confirm) {
      setErrorMessage(isFr ? 'Les mots de passe ne correspondent pas.' : 'Passwords do not match.');
      return;
    }
    runAction(
      async () => {
        await updatePassword(newPassword.password);
        toast({ title: isFr ? 'Mot de passe modifié' : 'Password updated' });
        handleAuthenticated();
      },
      'Modification impossible. Réessayez.',
      'Unable to update. Try again.'
    );
  };

  const handleDelete = () =>
    runAction(
      async () => {
        await deleteAccount();
        toast({ title: isFr ? 'Compte supprimé' : 'Account deleted' });
        handleClose();
      },
      'Suppression impossible pour le moment. Réessayez.',
      'Unable to delete right now. Try again.'
    );

  const infoStyle = {
    marginTop: 12,
    padding: '12px 14px',
    borderRadius: 8,
    border: '1px solid var(--afcfta-border)',
    fontSize: 14,
    lineHeight: 1.6,
  };

  const errorBox = errorMessage && (
    <div
      role="alert"
      data-testid="auth-error"
      style={{
        marginTop: 12,
        padding: '10px 12px',
        borderRadius: 8,
        border: '1px solid rgba(220, 38, 38, 0.35)',
        background: 'rgba(220, 38, 38, 0.08)',
        color: 'var(--text)',
        fontSize: 13,
      }}
    >
      {errorMessage}
    </div>
  );

  let panel = null;
  if (recovery) {
    panel = (
      <form className="space-y-4 pt-2" onSubmit={handleNewPassword} data-testid="recovery-form">
        {errorBox}
        <div className="space-y-1">
          <Label htmlFor="new-password">{isFr ? 'Nouveau mot de passe' : 'New password'}</Label>
          <Input
            id="new-password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            value={newPassword.password}
            onChange={(e) => setNewPassword({ ...newPassword, password: e.target.value })}
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="new-password-confirm">{isFr ? 'Confirmer' : 'Confirm'}</Label>
          <Input
            id="new-password-confirm"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            value={newPassword.confirm}
            onChange={(e) => setNewPassword({ ...newPassword, confirm: e.target.value })}
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {isFr ? 'Enregistrer le nouveau mot de passe' : 'Save new password'}
        </Button>
      </form>
    );
  } else if (user) {
    panel = (
      <div className="space-y-3 pt-2" data-testid="account-panel">
        {errorBox}
        <div style={infoStyle}>
          <strong>{user.name}</strong>
          <br />
          {user.email}
        </div>
        {view === 'confirmDelete' ? (
          <div style={{ ...infoStyle, borderColor: 'rgba(220, 38, 38, 0.5)' }}>
            {isFr
              ? 'Votre compte, vos clés API et vos données personnelles seront définitivement supprimés, et vos abonnements résiliés. Cette action est irréversible.'
              : 'Your account, API keys and personal data will be permanently deleted and your subscriptions canceled. This cannot be undone.'}
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <Button variant="outline" className="flex-1" onClick={() => setView(null)} disabled={loading}>
                {isFr ? 'Annuler' : 'Cancel'}
              </Button>
              <Button
                variant="destructive"
                className="flex-1"
                onClick={handleDelete}
                disabled={loading}
                data-testid="confirm-delete-btn"
              >
                {isFr ? 'Supprimer définitivement' : 'Delete permanently'}
              </Button>
            </div>
          </div>
        ) : (
          <>
            <Button
              variant="outline"
              className="w-full"
              disabled={loading}
              data-testid="export-account-btn"
              onClick={() => runAction(exportAccount, 'Export impossible. Réessayez.', 'Export failed. Try again.')}
            >
              {isFr ? 'Télécharger mes données' : 'Download my data'}
            </Button>
            <Button
              variant="outline"
              className="w-full"
              onClick={async () => {
                await logout();
                handleClose();
              }}
              data-testid="account-logout-btn"
            >
              {isFr ? 'Se déconnecter' : 'Log out'}
            </Button>
            <Button
              variant="ghost"
              className="w-full"
              style={{ color: 'rgb(220, 38, 38)' }}
              onClick={() => setView('confirmDelete')}
              data-testid="delete-account-btn"
            >
              {isFr ? 'Supprimer mon compte' : 'Delete my account'}
            </Button>
          </>
        )}
      </div>
    );
  } else if (view === 'confirm' || view === 'forgotSent') {
    panel = (
      <div style={infoStyle} role="status" data-testid="auth-info">
        {view === 'confirm'
          ? isFr
            ? 'Compte créé ! Cliquez sur le lien que nous venons de vous envoyer par email pour l\'activer, puis connectez-vous.'
            : 'Account created! Click the link we just emailed you to activate it, then sign in.'
          : isFr
            ? 'Si un compte existe pour cette adresse, un email de réinitialisation vient de vous être envoyé.'
            : 'If an account exists for this address, a reset email has just been sent.'}
        <Button
          variant="outline"
          className="w-full"
          style={{ marginTop: 12 }}
          onClick={() => {
            setView(null);
            setTab('login');
          }}
        >
          {isFr ? 'Retour à la connexion' : 'Back to sign in'}
        </Button>
      </div>
    );
  } else if (view === 'forgot') {
    panel = (
      <form className="space-y-4 pt-2" onSubmit={handleForgot} data-testid="forgot-form">
        {errorBox}
        <div className="space-y-1">
          <Label htmlFor="forgot-email">Email</Label>
          <Input
            id="forgot-email"
            type="email"
            autoComplete="username"
            required
            maxLength={254}
            value={forgotEmail}
            onChange={(e) => setForgotEmail(e.target.value)}
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {isFr ? 'Recevoir un lien de réinitialisation' : 'Send reset link'}
        </Button>
        <Button type="button" variant="ghost" className="w-full" onClick={() => setView(null)}>
          {isFr ? 'Retour' : 'Back'}
        </Button>
      </form>
    );
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent
        className="sm:max-w-md"
        data-testid="auth-modal"
        style={{
          background: 'var(--afcfta-card)',
          color: 'var(--text)',
          border: '1px solid var(--afcfta-border)',
        }}
      >
        <DialogHeader>
          <DialogTitle style={{ color: 'var(--text)' }}>{isFr ? 'Mon compte' : 'My account'}</DialogTitle>
          <DialogDescription style={{ color: 'var(--afcfta-muted)' }}>
            {recovery
              ? isFr ? 'Choisissez votre nouveau mot de passe.' : 'Choose your new password.'
              : user
                ? isFr ? 'Gérez votre compte et vos données personnelles.' : 'Manage your account and personal data.'
                : isFr ? 'Connectez-vous ou créez un compte pour continuer.' : 'Sign in or create an account to continue.'}
          </DialogDescription>
        </DialogHeader>

        {panel || (
        <Tabs
          value={tab}
          onValueChange={(value) => {
            setTab(value);
            setErrorMessage('');
          }}
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login" data-testid="auth-tab-login">{isFr ? 'Connexion' : 'Login'}</TabsTrigger>
            <TabsTrigger value="register" data-testid="auth-tab-register">{isFr ? 'Inscription' : 'Register'}</TabsTrigger>
          </TabsList>

          {errorMessage && (
            <div
              role="alert"
              data-testid="auth-error"
              style={{
                marginTop: 12,
                padding: '10px 12px',
                borderRadius: 8,
                border: '1px solid rgba(220, 38, 38, 0.35)',
                background: 'rgba(220, 38, 38, 0.08)',
                color: 'var(--text)',
                fontSize: 13,
              }}
            >
              {errorMessage}
            </div>
          )}

          <TabsContent value="login">
            <form className="space-y-4 pt-2" onSubmit={handleLogin}>
              <div className="space-y-1">
                <Label htmlFor="login-email">Email</Label>
                <Input
                  id="login-email"
                  type="email"
                  name="email"
                  autoComplete="username"
                  maxLength={254}
                  required
                  data-testid="login-email-input"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="login-password">{isFr ? 'Mot de passe' : 'Password'}</Label>
                <Input
                  id="login-password"
                  type="password"
                  name="password"
                  autoComplete="current-password"
                  maxLength={128}
                  required
                  data-testid="login-password-input"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading} aria-busy={loading} data-testid="login-submit-btn">
                {loading ? (isFr ? 'Connexion…' : 'Signing in…') : isFr ? 'Se connecter' : 'Sign in'}
              </Button>
              {supabaseEnabled && (
                <button
                  type="button"
                  onClick={() => {
                    setErrorMessage('');
                    setForgotEmail(loginForm.email);
                    setView('forgot');
                  }}
                  data-testid="forgot-password-link"
                  style={{ background: 'none', border: 'none', color: 'var(--afcfta-muted)', fontSize: 13, cursor: 'pointer', width: '100%' }}
                >
                  {isFr ? 'Mot de passe oublié ?' : 'Forgot password?'}
                </button>
              )}
            </form>
          </TabsContent>

          <TabsContent value="register">
            <form className="space-y-4 pt-2" onSubmit={handleRegister}>
              <div className="space-y-1">
                <Label htmlFor="register-name">{isFr ? 'Nom' : 'Name'}</Label>
                <Input
                  id="register-name"
                  name="name"
                  autoComplete="name"
                  maxLength={100}
                  required
                  data-testid="register-name-input"
                  value={registerForm.name}
                  onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="register-email">Email</Label>
                <Input
                  id="register-email"
                  type="email"
                  name="email"
                  autoComplete="email"
                  maxLength={254}
                  required
                  data-testid="register-email-input"
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="register-password">{isFr ? 'Mot de passe (8 caractères min.)' : 'Password (min. 8 chars)'}</Label>
                <Input
                  id="register-password"
                  type="password"
                  name="password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  maxLength={128}
                  data-testid="register-password-input"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="register-confirm-password">
                  {isFr ? 'Confirmer le mot de passe' : 'Confirm password'}
                </Label>
                <Input
                  id="register-confirm-password"
                  type="password"
                  name="confirm-password"
                  autoComplete="new-password"
                  required
                  minLength={8}
                  maxLength={128}
                  data-testid="register-confirm-password-input"
                  value={registerForm.confirmPassword}
                  onChange={(e) => setRegisterForm({ ...registerForm, confirmPassword: e.target.value })}
                />
              </div>
              <label
                htmlFor="register-accept-terms"
                style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 13, lineHeight: 1.5 }}
              >
                <input
                  id="register-accept-terms"
                  type="checkbox"
                  data-testid="register-accept-terms"
                  checked={registerForm.acceptTerms}
                  onChange={(e) => setRegisterForm({ ...registerForm, acceptTerms: e.target.checked })}
                  style={{ marginTop: 3 }}
                />
                <span>
                  {isFr ? 'J\'accepte les ' : 'I accept the '}
                  <a href="/cgu.html" target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'underline' }}>
                    {isFr ? 'conditions d\'utilisation' : 'terms of use'}
                  </a>
                  {isFr ? ' et la ' : ' and the '}
                  <a href="/confidentialite.html" target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'underline' }}>
                    {isFr ? 'politique de confidentialité' : 'privacy policy'}
                  </a>
                  .
                </span>
              </label>
              <Button type="submit" className="w-full" disabled={loading} aria-busy={loading} data-testid="register-submit-btn">
                {loading ? (isFr ? 'Création…' : 'Creating…') : isFr ? 'Créer mon compte' : 'Create account'}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}
