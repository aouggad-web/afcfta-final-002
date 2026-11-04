import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Button } from '../ui/button';
import { useAuth, formatApiErrorDetail } from '../../context/AuthContext';
import { toast } from '../../hooks/use-toast';
import { pick } from '../../i18n/lang';

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
    getSubscription,
    openBillingPortal,
  } = useAuth();
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
  const [subscription, setSubscription] = useState(null);

  useEffect(() => {
    if (!open || !user || !getSubscription) return;
    getSubscription().then(setSubscription).catch(() => setSubscription(null));
  }, [open, user, getSubscription]);

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
      toast({ title: pick(language, 'Connecté', 'Logged in', 'تم تسجيل الدخول'), description: pick(language, 'Bienvenue !', 'Welcome back!', 'مرحبًا بعودتك!') });
      handleAuthenticated();
    } catch (err) {
      const description = formatApiErrorDetail(
        err.response?.data?.detail,
        pick(language, 'Connexion impossible. Vérifiez votre accès réseau et réessayez.', 'Unable to sign in. Check your connection and try again.', 'تعذّر تسجيل الدخول. تحقّق من اتصالك بالشبكة وأعد المحاولة.')
      );
      setErrorMessage(description);
      toast({
        title: pick(language, 'Erreur de connexion', 'Login error', 'خطأ في تسجيل الدخول'),
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
      setErrorMessage(pick(language, 'Veuillez indiquer votre nom.', 'Please enter your name.', 'يرجى إدخال اسمك.'));
      return;
    }
    if (registerForm.password !== registerForm.confirmPassword) {
      setErrorMessage(pick(language, 'Les mots de passe ne correspondent pas.', 'Passwords do not match.', 'كلمتا المرور غير متطابقتين.'));
      return;
    }
    if (!registerForm.acceptTerms) {
      setErrorMessage(
        pick(language, 'Veuillez accepter les conditions d\'utilisation et la politique de confidentialité.', 'Please accept the terms of use and the privacy policy.', 'يرجى قبول شروط الاستخدام وسياسة الخصوصية.')
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
        title: pick(language, 'Compte créé', 'Account created', 'تم إنشاء الحساب'),
        description: pick(language, 'Bienvenue sur ZLECAf Intelligence !', 'Welcome to ZLECAf Intelligence!', 'مرحبًا بك في ZLECAf Intelligence!'),
      });
      handleAuthenticated();
    } catch (err) {
      const description = formatApiErrorDetail(
        err.response?.data?.detail,
        pick(language, 'Inscription impossible. Vérifiez votre accès réseau et réessayez.', 'Unable to register. Check your connection and try again.', 'تعذّر إنشاء الحساب. تحقّق من اتصالك بالشبكة وأعد المحاولة.')
      );
      setErrorMessage(description);
      toast({
        title: pick(language, 'Erreur d\'inscription', 'Registration error', 'خطأ في إنشاء الحساب'),
        description,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const runAction = async (action, fallbackFr, fallbackEn, fallbackAr) => {
    setErrorMessage('');
    setLoading(true);
    try {
      await action();
    } catch (err) {
      setErrorMessage(formatApiErrorDetail(err.response?.data?.detail, pick(language, fallbackFr, fallbackEn, fallbackAr)));
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
      'Unable to send. Try again in a few minutes.',
      'تعذّر الإرسال. أعد المحاولة بعد بضع دقائق.'
    );
  };

  const handleNewPassword = (e) => {
    e.preventDefault();
    if (newPassword.password !== newPassword.confirm) {
      setErrorMessage(pick(language, 'Les mots de passe ne correspondent pas.', 'Passwords do not match.', 'كلمتا المرور غير متطابقتين.'));
      return;
    }
    runAction(
      async () => {
        await updatePassword(newPassword.password);
        toast({ title: pick(language, 'Mot de passe modifié', 'Password updated', 'تم تغيير كلمة المرور') });
        handleAuthenticated();
      },
      'Modification impossible. Réessayez.',
      'Unable to update. Try again.',
      'تعذّر التعديل. أعد المحاولة.'
    );
  };

  const handleDelete = () =>
    runAction(
      async () => {
        await deleteAccount();
        toast({ title: pick(language, 'Compte supprimé', 'Account deleted', 'تم حذف الحساب') });
        handleClose();
      },
      'Suppression impossible pour le moment. Réessayez.',
      'Unable to delete right now. Try again.',
      'تعذّر الحذف حاليًا. أعد المحاولة.'
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
          <Label htmlFor="new-password">{pick(language, 'Nouveau mot de passe', 'New password', 'كلمة المرور الجديدة')}</Label>
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
          <Label htmlFor="new-password-confirm">{pick(language, 'Confirmer', 'Confirm', 'تأكيد')}</Label>
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
          {pick(language, 'Enregistrer le nouveau mot de passe', 'Save new password', 'حفظ كلمة المرور الجديدة')}
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
        {subscription && (
          <SubscriptionBlock
            subscription={subscription}
            language={language}
            infoStyle={infoStyle}
            loading={loading}
            onManage={() =>
              runAction(
                openBillingPortal,
                'Espace de gestion indisponible. Réessayez.',
                'Billing portal unavailable. Try again.',
                'بوابة إدارة الاشتراك غير متاحة. أعد المحاولة.'
              )
            }
          />
        )}
        {view === 'confirmDelete' ? (
          <div style={{ ...infoStyle, borderColor: 'rgba(220, 38, 38, 0.5)' }}>
            {pick(language, 'Votre compte, vos clés API et vos données personnelles seront définitivement supprimés, et vos abonnements résiliés. Cette action est irréversible.', 'Your account, API keys and personal data will be permanently deleted and your subscriptions canceled. This cannot be undone.', 'سيتم حذف حسابك ومفاتيح API الخاصة بك وبياناتك الشخصية نهائيًا، وإلغاء اشتراكاتك. لا يمكن التراجع عن هذا الإجراء.')}
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <Button variant="outline" className="flex-1" onClick={() => setView(null)} disabled={loading}>
                {pick(language, 'Annuler', 'Cancel', 'إلغاء')}
              </Button>
              <Button
                variant="destructive"
                className="flex-1"
                onClick={handleDelete}
                disabled={loading}
                data-testid="confirm-delete-btn"
              >
                {pick(language, 'Supprimer définitivement', 'Delete permanently', 'حذف نهائي')}
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
              onClick={() => runAction(exportAccount, 'Export impossible. Réessayez.', 'Export failed. Try again.', 'تعذّر التصدير. أعد المحاولة.')}
            >
              {pick(language, 'Télécharger mes données', 'Download my data', 'تنزيل بياناتي')}
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
              {pick(language, 'Se déconnecter', 'Log out', 'تسجيل الخروج')}
            </Button>
            <Button
              variant="ghost"
              className="w-full"
              style={{ color: 'rgb(220, 38, 38)' }}
              onClick={() => setView('confirmDelete')}
              data-testid="delete-account-btn"
            >
              {pick(language, 'Supprimer mon compte', 'Delete my account', 'حذف حسابي')}
            </Button>
          </>
        )}
      </div>
    );
  } else if (view === 'confirm' || view === 'forgotSent') {
    panel = (
      <div style={infoStyle} role="status" data-testid="auth-info">
        {view === 'confirm'
          ? pick(language, 'Compte créé ! Cliquez sur le lien que nous venons de vous envoyer par email pour l\'activer, puis connectez-vous.', 'Account created! Click the link we just emailed you to activate it, then sign in.', 'تم إنشاء الحساب! انقر على الرابط الذي أرسلناه إليك للتو عبر البريد الإلكتروني لتفعيله، ثم سجّل الدخول.')
          : pick(language, 'Si un compte existe pour cette adresse, un email de réinitialisation vient de vous être envoyé.', 'If an account exists for this address, a reset email has just been sent.', 'إذا كان هناك حساب مرتبط بهذا العنوان، فقد أُرسلت إليك للتو رسالة إعادة تعيين كلمة المرور.')}
        <Button
          variant="outline"
          className="w-full"
          style={{ marginTop: 12 }}
          onClick={() => {
            setView(null);
            setTab('login');
          }}
        >
          {pick(language, 'Retour à la connexion', 'Back to sign in', 'العودة إلى تسجيل الدخول')}
        </Button>
      </div>
    );
  } else if (view === 'forgot') {
    panel = (
      <form className="space-y-4 pt-2" onSubmit={handleForgot} data-testid="forgot-form">
        {errorBox}
        <div className="space-y-1">
          <Label htmlFor="forgot-email">{pick(language, 'Email', 'Email', 'البريد الإلكتروني')}</Label>
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
          {pick(language, 'Recevoir un lien de réinitialisation', 'Send reset link', 'إرسال رابط إعادة التعيين')}
        </Button>
        <Button type="button" variant="ghost" className="w-full" onClick={() => setView(null)}>
          {pick(language, 'Retour', 'Back', 'رجوع')}
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
          <DialogTitle style={{ color: 'var(--text)' }}>{pick(language, 'Mon compte', 'My account', 'حسابي')}</DialogTitle>
          <DialogDescription style={{ color: 'var(--afcfta-muted)' }}>
            {recovery
              ? pick(language, 'Choisissez votre nouveau mot de passe.', 'Choose your new password.', 'اختر كلمة المرور الجديدة.')
              : user
                ? pick(language, 'Gérez votre compte et vos données personnelles.', 'Manage your account and personal data.', 'أدِر حسابك وبياناتك الشخصية.')
                : pick(language, 'Connectez-vous ou créez un compte pour continuer.', 'Sign in or create an account to continue.', 'سجّل الدخول أو أنشئ حسابًا للمتابعة.')}
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
            <TabsTrigger value="login" data-testid="auth-tab-login">{pick(language, 'Connexion', 'Login', 'تسجيل الدخول')}</TabsTrigger>
            <TabsTrigger value="register" data-testid="auth-tab-register">{pick(language, 'Inscription', 'Register', 'إنشاء حساب')}</TabsTrigger>
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
                <Label htmlFor="login-email">{pick(language, 'Email', 'Email', 'البريد الإلكتروني')}</Label>
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
                <Label htmlFor="login-password">{pick(language, 'Mot de passe', 'Password', 'كلمة المرور')}</Label>
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
                {loading ? (pick(language, 'Connexion…', 'Signing in…', 'جارٍ تسجيل الدخول…')) : pick(language, 'Se connecter', 'Sign in', 'تسجيل الدخول')}
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
                  {pick(language, 'Mot de passe oublié ?', 'Forgot password?', 'نسيت كلمة المرور؟')}
                </button>
              )}
            </form>
          </TabsContent>

          <TabsContent value="register">
            <form className="space-y-4 pt-2" onSubmit={handleRegister}>
              <div className="space-y-1">
                <Label htmlFor="register-name">{pick(language, 'Nom', 'Name', 'الاسم')}</Label>
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
                <Label htmlFor="register-email">{pick(language, 'Email', 'Email', 'البريد الإلكتروني')}</Label>
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
                <Label htmlFor="register-password">{pick(language, 'Mot de passe (8 caractères min.)', 'Password (min. 8 chars)', 'كلمة المرور (8 أحرف على الأقل)')}</Label>
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
                  {pick(language, 'Confirmer le mot de passe', 'Confirm password', 'تأكيد كلمة المرور')}
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
                  {pick(language, 'J\'accepte les ', 'I accept the ', 'أوافق على ')}
                  <a href="/cgu.html" target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'underline' }}>
                    {pick(language, 'conditions d\'utilisation', 'terms of use', 'شروط الاستخدام')}
                  </a>
                  {pick(language, ' et la ', ' and the ', ' و')}
                  <a href="/confidentialite.html" target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'underline' }}>
                    {pick(language, 'politique de confidentialité', 'privacy policy', 'سياسة الخصوصية')}
                  </a>
                  .
                </span>
              </label>
              <Button type="submit" className="w-full" disabled={loading} aria-busy={loading} data-testid="register-submit-btn">
                {loading ? (pick(language, 'Création…', 'Creating…', 'جارٍ الإنشاء…')) : pick(language, 'Créer mon compte', 'Create account', 'إنشاء حساب')}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}

// « admin » : compte admin amorcé, tous les modules sans quota (hors grille vendue).
const PLAN_LABELS = { free: 'Free', starter: 'Starter', pro: 'Pro', business: 'Business', admin: 'Admin' };

function formatDate(value, language) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toLocaleDateString(pick(language, 'fr-FR', 'en-GB', 'ar-u-nu-latn'));
}

// Bloc « Mon abonnement » : formule en cours, échéance, et accès à la gestion
// (espace client Stripe pour la carte, les factures, le changement de formule
// et la résiliation ; page tarifs pour souscrire ou renouveler via Chargily).
function SubscriptionBlock({ subscription, language, infoStyle, loading, onManage }) {
  const tier = subscription.effective_tier || 'free';
  const isPaid = tier !== 'free';
  const endDate = formatDate(subscription.current_period_end, language);
  const cycle = subscription.cycle === 'annual' ? (pick(language, 'annuel', 'yearly', 'سنوي')) : pick(language, 'mensuel', 'monthly', 'شهري');

  let detail = null;
  if (isPaid && subscription.status === 'past_due') {
    detail = pick(language, 'Le dernier paiement a échoué : mettez à jour votre carte pour garder votre accès.', 'Your last payment failed: update your card to keep your access.', 'فشلت عملية الدفع الأخيرة: حدِّث بطاقتك للحفاظ على وصولك.');
  } else if (isPaid && subscription.cancel_at_period_end && endDate) {
    detail = pick(language, `Résiliation programmée : accès jusqu'au ${endDate}.`, `Canceled: access until ${endDate}.`, `الإلغاء مُجدول: الوصول متاح حتى ${endDate}.`);
  } else if (isPaid && endDate) {
    detail =
      subscription.payment_provider === 'stripe'
        ? pick(language, `Prochain renouvellement le ${endDate}.`, `Renews on ${endDate}.`, `التجديد القادم في ${endDate}.`)
        : pick(language, `Valable jusqu'au ${endDate} (sans renouvellement automatique).`, `Valid until ${endDate} (no automatic renewal).`, `صالح حتى ${endDate} (دون تجديد تلقائي).`);
  }

  return (
    <div style={infoStyle} data-testid="subscription-block">
      <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, opacity: 0.7 }}>
        {pick(language, 'Mon abonnement', 'My subscription', 'اشتراكي')}
      </div>
      <strong>
        {pick(language, 'Formule ', 'Plan ', 'الباقة ')}
        {PLAN_LABELS[tier] || tier}
        {isPaid && tier !== 'admin' ? ` · ${cycle}` : ''}
      </strong>
      {detail && <div style={{ fontSize: 13, marginTop: 4 }}>{detail}</div>}
      <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
        {subscription.can_manage_billing && subscription.payment_provider !== 'chargily' && (
          <Button className="flex-1" onClick={onManage} disabled={loading} data-testid="manage-billing-btn">
            {pick(language, 'Gérer mon abonnement', 'Manage subscription', 'إدارة اشتراكي')}
          </Button>
        )}
        {(!isPaid || subscription.payment_provider === 'chargily') && (
          <Button variant="outline" className="flex-1" onClick={() => { window.location.href = '/pricing.html'; }}>
            {isPaid ? (pick(language, 'Renouveler', 'Renew', 'تجديد')) : pick(language, 'Voir les formules', 'See plans', 'عرض الباقات')}
          </Button>
        )}
      </div>
    </div>
  );
}

