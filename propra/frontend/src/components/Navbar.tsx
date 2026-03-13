import { Link, useLocation } from "react-router-dom";
import { Scale, Menu, X } from "lucide-react";
import { useState } from "react";
import { useLanguage } from "@/context/LanguageContext";

const Navbar = () => {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { lang, setLang, t } = useLanguage();

  const links = [
    { to: "/", label: t("nav.home") },
    { to: "/advisor", label: t("nav.advisor") },
    { to: "/permits", label: t("nav.permits") },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-navy/95 backdrop-blur-sm border-b border-gold/20">
      <div className="container mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded bg-gold/20 border border-gold/40 flex items-center justify-center group-hover:bg-gold/30 transition-colors">
            <Scale className="w-4 h-4 text-gold" />
          </div>
          <span className="font-display font-bold text-primary-foreground text-lg tracking-tight">
            Recht<span className="text-gold">Immobilien</span>
          </span>
        </Link>

        {/* Desktop */}
        <div className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`px-4 py-2 rounded text-sm font-body font-medium transition-all ${
                location.pathname === l.to
                  ? "bg-gold/20 text-gold"
                  : "text-primary-foreground/70 hover:text-primary-foreground hover:bg-white/5"
              }`}
            >
              {l.label}
            </Link>
          ))}

          {/* Language toggle */}
          <div className="ml-4 flex items-center rounded-lg border border-gold/30 overflow-hidden bg-gold/5">
            <button
              onClick={() => setLang("en")}
              className={`px-3 py-1.5 text-xs font-body font-semibold transition-all ${
                lang === "en"
                  ? "bg-gold text-accent-foreground"
                  : "text-primary-foreground/60 hover:text-primary-foreground"
              }`}
            >
              EN
            </button>
            <div className="w-px h-4 bg-gold/25" />
            <button
              onClick={() => setLang("de")}
              className={`px-3 py-1.5 text-xs font-body font-semibold transition-all ${
                lang === "de"
                  ? "bg-gold text-accent-foreground"
                  : "text-primary-foreground/60 hover:text-primary-foreground"
              }`}
            >
              DE
            </button>
          </div>
        </div>

        {/* Mobile */}
        <div className="md:hidden flex items-center gap-3">
          {/* Mobile language toggle */}
          <div className="flex items-center rounded-md border border-gold/30 overflow-hidden bg-gold/5">
            <button
              onClick={() => setLang("en")}
              className={`px-2.5 py-1 text-xs font-body font-semibold transition-all ${
                lang === "en"
                  ? "bg-gold text-accent-foreground"
                  : "text-primary-foreground/60"
              }`}
            >
              EN
            </button>
            <div className="w-px h-3.5 bg-gold/25" />
            <button
              onClick={() => setLang("de")}
              className={`px-2.5 py-1 text-xs font-body font-semibold transition-all ${
                lang === "de"
                  ? "bg-gold text-accent-foreground"
                  : "text-primary-foreground/60"
              }`}
            >
              DE
            </button>
          </div>
          <button
            className="text-primary-foreground/70 hover:text-primary-foreground"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-navy border-t border-gold/20 py-4 px-6 flex flex-col gap-2">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setMobileOpen(false)}
              className={`px-4 py-2 rounded text-sm font-body font-medium transition-all ${
                location.pathname === l.to
                  ? "bg-gold/20 text-gold"
                  : "text-primary-foreground/70 hover:text-primary-foreground"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
