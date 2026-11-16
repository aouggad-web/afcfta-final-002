import React, { useState } from "react";
import {
  LayoutDashboard,
  Calculator,
  BarChart3,
  Factory,
  Ship,
  Landmark,
  Wrench,
  FileCheck,
  Globe2,
  Menu,
  Moon,
  Sun,
  TrendingUp,
  X,
  Mail,
  User,
  Tag,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { pick } from "../i18n/lang";

/* ─── Flat nav items ─────────────────────────────────────────── */
const NAV_ITEMS = (lang) => [
  { id: "dashboard",  label: pick(lang, "Tableau de bord", "Dashboard", "لوحة القيادة"),      icon: LayoutDashboard },
  { id: "calculator", label: pick(lang, "Calculateur", "Calculator", "الحاسبة"),     icon: Calculator },
  { id: "stats",      label: pick(lang, "Statistiques", "Statistics", "الإحصائيات"),     icon: BarChart3 },
  { id: "production", label: pick(lang, "Production", "Production", "الإنتاج"),     icon: Factory },
  { id: "logistics",  label: pick(lang, "Logistique", "Logistics", "اللوجستيك"),      icon: Ship },
  { id: "banking",    label: pick(lang, "Finance", "Finance", "التمويل"),        icon: Landmark },
  { id: "tools",      label: pick(lang, "Outils", "Tools", "الأدوات"),          icon: Wrench },
  { id: "roo",        label: pick(lang, "R. d'Origine", "Rules of Origin", "قواعد المنشأ"),icon: FileCheck },
  { id: "profiles",   label: pick(lang, "Profils", "Profiles", "ملفات البلدان"),       icon: Globe2 },
  { id: "reports",    label: pick(lang, "Opportunités", "Opportunities", "الفرص"),  icon: TrendingUp },
  { id: "contact",    label: pick(lang, "Contact", "Contact", "اتصل بنا"),        icon: Mail },
];

/* ─── Langues de l'interface ─────────────────────────────────── */
const LANG_BUTTONS = [
  { code: "fr", label: "FR", name: "Français" },
  { code: "en", label: "EN", name: "English" },
  { code: "ar", label: "ع", name: "العربية" },
];

/* ─── Horizontal topbar component ───────────────────────────── */
export default function AfcftaTopbar({ active = "dashboard", onTabChange, language = "fr", theme = "dark", onThemeToggle, onOpenAuth }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const isLight = theme === "light";
  const items = NAV_ITEMS(language);
  const { user } = useAuth() || {};

  const handleTab = (id) => {
    onTabChange && onTabChange("tab", id);
    setMobileOpen(false);
  };

  return (
    <header className="afcfta-topHeader" role="banner">
      {/* ── Brand + language bar ── */}
      <div className="afcfta-topHeader__bar">
        <div className="afcfta-topHeader__brand">
          <img
            className="afcfta-topHeader__brandIcon afcfta-sidebar-brandmark"
            src="/brand/logo.svg"
            alt=""
            width={32}
            height={32}
          />
          <span className="afcfta-topHeader__brandName">
            {pick(language, "ZLECAf Intelligence", "AfCFTA Intelligence", "ZLECAf Intelligence")}
          </span>
        </div>

        {/* Mobile menu toggle */}
        <button
          className="afcfta-btn-sm afcfta-btn-secondary afcfta-topHeader__menuBtn"
          onClick={() => setMobileOpen((o) => !o)}
          aria-label={mobileOpen
            ? pick(language, "Fermer le menu", "Close menu", "إغلاق القائمة")
            : pick(language, "Ouvrir le menu", "Open menu", "فتح القائمة")}
          style={{ padding: "8px", borderRadius: "8px" }}
          aria-expanded={mobileOpen}
          aria-controls="afcfta-mobile-nav"
          id="afcfta-mobile-menu-btn"
        >
          {mobileOpen ? <X size={18} /> : <Menu size={18} />}
        </button>

        <div className="afcfta-topHeader__lang">
          <a
            href="/pricing.html"
            className="afcfta-btn-sm afcfta-btn-secondary"
            data-testid="topbar-pricing-link"
            style={{ display: "flex", alignItems: "center", gap: 6, textDecoration: "none" }}
          >
            <Tag size={14} />
            <span className="afcfta-pricing-label">{pick(language, "Tarifs", "Pricing", "الأسعار")}</span>
          </a>
          {user ? (
            <button
              className="afcfta-btn-sm afcfta-btn-secondary"
              onClick={onOpenAuth}
              title={pick(language, "Mon compte", "My account", "حسابي")}
              data-testid="topbar-account-btn"
              style={{ display: "flex", alignItems: "center", gap: 6 }}
            >
              <User size={14} /> <span className="afcfta-account-label">{user.name}</span>
            </button>
          ) : (
            <button
              className="afcfta-btn-sm afcfta-btn-secondary"
              onClick={onOpenAuth}
              aria-label={pick(language, "Connexion", "Login", "تسجيل الدخول")}
              data-testid="topbar-login-btn"
              style={{ display: "flex", alignItems: "center", gap: 6 }}
            >
              <User size={14} /> <span className="afcfta-account-label">{pick(language, "Connexion", "Login", "تسجيل الدخول")}</span>
            </button>
          )}
          {onThemeToggle && (
            <button
              className="afcfta-themeToggle"
              onClick={onThemeToggle}
              aria-label={isLight
                ? pick(language, "Activer le mode sombre", "Switch to dark mode", "تفعيل الوضع الداكن")
                : pick(language, "Activer le mode clair", "Switch to light mode", "تفعيل الوضع الفاتح")}
              title={isLight
                ? pick(language, "Mode sombre", "Dark mode", "الوضع الداكن")
                : pick(language, "Mode clair", "Light mode", "الوضع الفاتح")}
              data-testid="theme-toggle-btn"
            >
              {isLight ? <Moon size={16} /> : <Sun size={16} />}
            </button>
          )}
          {LANG_BUTTONS.map(({ code, label, name }) => (
            <button
              key={code}
              className={`afcfta-langBtn ${language === code ? "active" : ""}`}
              onClick={() => onTabChange && onTabChange("language", code)}
              aria-pressed={language === code}
              title={name}
              lang={code}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Horizontal nav tabs ── */}
      <nav
        className="afcfta-topHeader__nav"
        aria-label={pick(language, "Navigation principale", "Main navigation", "التنقل الرئيسي")}
      >
        {items.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => handleTab(id)}
            className={`afcfta-navTab ${active === id ? "active" : ""}`}
            role="tab"
            aria-selected={active === id}
          >
            <Icon size={15} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      {/* ── Mobile dropdown nav ── */}
      {mobileOpen && (
        <>
          <div
            className="afcfta-sidebar-overlay"
            onClick={() => setMobileOpen(false)}
            style={{
              position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
              zIndex: 49, backdropFilter: "blur(2px)",
            }}
          />
          <div
            id="afcfta-mobile-nav"
            className="afcfta-mobile-nav-dropdown"
            style={{ display: "block" }}
          >
            <div className="afcfta-mobile-nav-list">
              {items.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => handleTab(id)}
                  className={`afcfta-mobile-nav-item ${active === id ? "active" : ""}`}
                  role="tab"
                  aria-selected={active === id}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </header>
  );
}
