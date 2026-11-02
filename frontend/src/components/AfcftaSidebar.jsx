import React, { useState } from "react";
import {
  LayoutDashboard, Calculator, BarChart3, Factory, Ship,
  Landmark, Wrench, FileCheck, Globe2, ChevronLeft, ChevronRight,
  Moon, Sun, TrendingUp, Mail, User, LogOut, Tag,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { pick, isRtl } from "../i18n/lang";

const NAV_ITEMS = (lang) => [
  { id: "dashboard",  label: pick(lang, "Tableau de bord", "Dashboard", "لوحة القيادة"),       icon: LayoutDashboard },
  { id: "calculator", label: pick(lang, "Calculateur", "Calculator", "الحاسبة"),      icon: Calculator },
  { id: "stats",      label: pick(lang, "Statistiques", "Statistics", "الإحصائيات"),      icon: BarChart3 },
  { id: "production", label: pick(lang, "Production", "Production", "الإنتاج"),      icon: Factory },
  { id: "logistics",  label: pick(lang, "Logistique", "Logistics", "اللوجستيك"),       icon: Ship },
  { id: "banking",    label: pick(lang, "Finance", "Finance", "التمويل"),         icon: Landmark },
  { id: "tools",      label: pick(lang, "Outils", "Tools", "الأدوات"),           icon: Wrench },
  { id: "roo",        label: pick(lang, "R. d'Origine", "Rules of Origin", "قواعد المنشأ"), icon: FileCheck },
  { id: "profiles",   label: pick(lang, "Profils", "Profiles", "ملفات البلدان"),        icon: Globe2 },
  { id: "reports",    label: pick(lang, "Opportunités", "Opportunities", "الفرص"),   icon: TrendingUp },
  { id: "contact",    label: pick(lang, "Contact", "Contact", "اتصل بنا"),         icon: Mail },
];

// Langues de l'interface.
const LANG_BUTTONS = [
  { code: "fr", label: "FR", name: "Français" },
  { code: "en", label: "EN", name: "English" },
  { code: "ar", label: "ع", name: "العربية" },
];

export default function AfcftaSidebar({
  active = "dashboard",
  onTabChange,
  language = "fr",
  theme = "dark",
  onThemeToggle,
  onOpenAuth,
}) {
  const [collapsed, setCollapsed] = useState(false);
  // En arabe la barre est à droite : les chevrons de repli s'inversent.
  const rtl = isRtl(language);
  const isLight = theme === "light";
  const items = NAV_ITEMS(language);
  const { user, logout } = useAuth() || {};

  const handleTab = (id) => {
    onTabChange && onTabChange("tab", id);
  };

  return (
    <aside className={`afcfta-sidebar${collapsed ? " collapsed" : ""}`}>
      {/* Logo */}
      <div className="afcfta-sidebar-logo">
        <img
          className="afcfta-sidebar-icon afcfta-sidebar-brandmark"
          src="/brand/logo.svg"
          alt=""
          width={38}
          height={38}
        />
        <div className="afcfta-sidebar-title">
          <h1>{pick(language, "ZLECAf", "AfCFTA", "زليكاف")}</h1>
          <p>{pick(language, "Intelligence commerciale", "Trade Intelligence", "المعلومات التجارية")}</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="afcfta-sidebar-nav" aria-label={pick(language, "Navigation principale", "Main navigation", "التنقل الرئيسي")}>
        {items.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => handleTab(id)}
            className={`afcfta-nav-item${active === id ? " active" : ""}`}
            role="tab"
            aria-selected={active === id}
            title={collapsed ? label : undefined}
            data-testid={`sidebar-nav-${id}`}
          >
            <span className="afcfta-nav-icon">
              <Icon size={16} strokeWidth={1.7} />
            </span>
            <span className="afcfta-nav-label">{label}</span>
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="afcfta-sidebar-footer">
        {/* Pricing */}
        <a
          href="/pricing.html"
          className="afcfta-nav-item"
          style={{ marginBottom: 8, width: "100%", textDecoration: "none" }}
          data-testid="sidebar-pricing-link"
        >
          <span className="afcfta-nav-icon"><Tag size={16} strokeWidth={1.7} /></span>
          <span className="afcfta-nav-label">{pick(language, "Tarifs", "Pricing", "الأسعار")}</span>
        </a>

        {/* Account */}
        {user ? (
          <div className="afcfta-nav-item" style={{ marginBottom: 8, cursor: "default" }} data-testid="sidebar-user-info">
            <span className="afcfta-nav-icon"><User size={16} strokeWidth={1.7} /></span>
            <button
              className="afcfta-nav-label"
              onClick={onOpenAuth}
              title={pick(language, "Mon compte", "My account", "حسابي")}
              data-testid="sidebar-account-btn"
              style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", background: "none", border: "none", color: "inherit", cursor: "pointer", textAlign: "left", padding: 0, font: "inherit" }}
            >
              {user.name}
            </button>
            <button
              onClick={logout}
              aria-label={pick(language, "Se déconnecter", "Log out", "تسجيل الخروج")}
              title={pick(language, "Se déconnecter", "Log out", "تسجيل الخروج")}
              data-testid="sidebar-logout-btn"
              style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", padding: 4 }}
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <button
            className="afcfta-nav-item"
            onClick={onOpenAuth}
            style={{ marginBottom: 8, width: "100%" }}
            data-testid="sidebar-login-btn"
          >
            <span className="afcfta-nav-icon"><User size={16} strokeWidth={1.7} /></span>
            <span className="afcfta-nav-label">{pick(language, "Connexion", "Login", "تسجيل الدخول")}</span>
          </button>
        )}

        {/* Language + theme */}
        <div className="afcfta-lang-switch" style={{ marginBottom: 8 }}>
          {LANG_BUTTONS.map(({ code, label, name }) => (
            <button
              key={code}
              className={`afcfta-langBtn${language === code ? " active" : ""}`}
              onClick={() => onTabChange && onTabChange("language", code)}
              aria-pressed={language === code}
              title={name}
              lang={code}
            >{label}</button>
          ))}
          {onThemeToggle && (
            <button
              className="afcfta-themeToggle"
              onClick={onThemeToggle}
              aria-label={isLight
                ? pick(language, "Mode sombre", "Dark mode", "الوضع الداكن")
                : pick(language, "Mode clair", "Light mode", "الوضع الفاتح")}
              style={{ marginInlineStart: "auto" }}
            >
              {isLight ? <Moon size={14} /> : <Sun size={14} />}
            </button>
          )}
        </div>

        {/* Collapse toggle */}
        <button
          className="afcfta-sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed
            ? pick(language, "Développer", "Expand", "توسيع")
            : pick(language, "Réduire", "Collapse", "طي")}
        >
          {collapsed !== rtl ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
          <span className="afcfta-sidebar-toggle-label">
            {pick(language, "Réduire", "Collapse", "طي")}
          </span>
        </button>
      </div>
    </aside>
  );
}
