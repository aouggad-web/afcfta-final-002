import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { useAuth, formatApiErrorDetail } from '../../context/AuthContext';
import { toast } from '../../hooks/use-toast';

export default function AuthModal({ open, onClose, onAuthenticated, language = 'fr' }) {
  const { login, register } = useAuth();
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
  });

  const resetForms = () => {
    setTab('login');
    setLoginForm({ email: '', password: '' });
    setRegisterForm({ name: '', email: '', password: '', confirmPassword: '' });
    setErrorMessage('');
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

    setLoading(true);
    try {
      await register(name, email, registerForm.password);
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
            {isFr ? 'Connectez-vous ou créez un compte pour continuer.' : 'Sign in or create an account to continue.'}
          </DialogDescription>
        </DialogHeader>

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
              <Button type="submit" className="w-full" disabled={loading} aria-busy={loading} data-testid="register-submit-btn">
                {loading ? (isFr ? 'Création…' : 'Creating…') : isFr ? 'Créer mon compte' : 'Create account'}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
