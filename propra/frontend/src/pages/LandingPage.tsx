import { Link } from "react-router-dom";
import { Scale, MessageSquare, FileCheck, Star, Shield, Zap, ChevronRight, BookOpen, Building2, FileSignature, CheckCircle2, Circle, Bell } from "lucide-react";
import { useState } from "react";
import hero1 from "@/assets/hero1.jpg";
import hero2 from "@/assets/hero2.jpg";
import hero3 from "@/assets/hero3.jpg";
import { useLanguage } from "@/context/LanguageContext";

const HERO_IMAGES = [hero1, hero2, hero3];

const PREVIEW_CASES = [
  {
    titleKey: "Widerspruch gegen Baugenehmigung Nachbar",
    status: "in_progress" as const,
    date: "12.02.2024",
    deadline: "15.03.2024",
    steps: [
      { label: "Dokument erstellt", done: true },
      { label: "Eingereicht beim Bauamt", done: true },
      { label: "Stellungnahme angefordert", done: false },
      { label: "Entscheidung ausstehend", done: false },
    ],
  },
  {
    titleKey: "Eigenbedarfskündigung – Rechtslage prüfen",
    status: "completed" as const,
    date: "08.01.2024",
    steps: [
      { label: "Rechtslage analysiert", done: true },
      { label: "Widerspruch formuliert", done: true },
      { label: "Einigung erzielt", done: true },
    ],
  },
  {
    titleKey: "Grunderwerbsteuer-Einspruch vorbereiten",
    status: "pending" as const,
    date: "28.02.2024",
    steps: [
      { label: "Unterlagen zusammenstellen", done: false },
      { label: "Einspruch einreichen", done: false },
      { label: "Finanzamt-Antwort abwarten", done: false },
    ],
  },
];

const LandingPage = () => {
  const { t } = useLanguage();
  const [heroBg] = useState(() => {
    const last = parseInt(localStorage.getItem("heroBgIndex") ?? "-1", 10);
    const next = (last + 1) % HERO_IMAGES.length;
    localStorage.setItem("heroBgIndex", String(next));
    return HERO_IMAGES[next];
  });

  const features = [
    { icon: MessageSquare, title: t("landing.feat1.title"), desc: t("landing.feat1.desc") },
    { icon: BookOpen, title: t("landing.feat2.title"), desc: t("landing.feat2.desc") },
    { icon: Shield, title: t("landing.feat3.title"), desc: t("landing.feat3.desc") },
    { icon: FileCheck, title: t("landing.feat4.title"), desc: t("landing.feat4.desc") },
    { icon: FileSignature, title: t("landing.feat5.title"), desc: t("landing.feat5.desc") },
  ];

  const stats = [
    { value: "3,784", label: t("landing.stat1") },
    { value: "16", label: t("landing.stat3") },
    { value: "24/7", label: t("landing.stat4") },
  ];

  const sampleQuestions = [
    t("advisor.q1"),
    t("advisor.q2"),
    t("advisor.q3"),
    t("advisor.q4"),
  ];

  const legalAreas = [
    { law: "LBO (alle 16 Bundesländer)", area: t("landing.area1") },
    { law: "BauGB §§ 1–246", area: t("landing.area2") },
    { law: "BauNVO", area: t("landing.area3") },
  ];

  const statusConfig = {
    in_progress: { label: t("status.in_progress"), className: "bg-blue-50 text-blue-700 border-blue-200" },
    completed: { label: t("status.completed"), className: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    pending: { label: t("status.pending"), className: "bg-amber-50 text-amber-700 border-amber-200" },
  };

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: `url(${heroBg})` }}
        />
        <div className="absolute inset-0" style={{ background: "linear-gradient(to right, hsl(222 60% 14% / 0.95) 0%, hsl(222 60% 14% / 0.75) 25%, hsl(222 60% 14% / 0.20) 50%, hsl(222 60% 14% / 0.05) 100%)" }} />
        <div className="absolute inset-0" style={{ background: "linear-gradient(to top, hsl(222 60% 14% / 0.60) 0%, transparent 60%)" }} />

        <div className="relative container mx-auto px-6 pt-24 pb-16">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-gold/30 bg-gold/10 mb-8 animate-fade-in">
              <span className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
              <span className="text-gold text-xs font-body font-medium tracking-wide uppercase">
                {t("landing.badge")}
              </span>
            </div>

            <h1 className="font-display text-5xl md:text-7xl font-bold text-primary-foreground leading-[1.05] mb-6 animate-fade-up">
              {t("landing.hero.line1")}
              <br />
              <span className="text-gold">{t("landing.hero.line2")}</span>
              <br />
              {t("landing.hero.line3")}
            </h1>

            <p className="font-body text-primary-foreground/90 text-lg md:text-xl leading-relaxed mb-10 max-w-xl animate-fade-up" style={{ animationDelay: "0.15s" }}>
              {t("landing.hero.sub")}
            </p>

            <div className="flex flex-wrap gap-4 animate-fade-up" style={{ animationDelay: "0.3s" }}>
              <Link
                to="/advisor"
                className="group inline-flex items-center gap-2 px-7 py-4 rounded-lg bg-gold text-accent-foreground font-body font-semibold text-base hover:bg-gold-light transition-all shadow-gold hover:shadow-lg hover:-translate-y-0.5"
              >
                {t("landing.hero.cta1")}
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/permits"
                className="inline-flex items-center gap-2 px-7 py-4 rounded-lg border border-primary-foreground/25 text-primary-foreground font-body font-medium text-base hover:bg-white/8 hover:border-primary-foreground/40 transition-all"
              >
                <FileCheck className="w-4 h-4" />
                {t("landing.hero.cta2")}
              </Link>
            </div>
          </div>
        </div>

        {/* Sample questions floating card */}
        <div className="hidden lg:block absolute right-12 top-1/2 -translate-y-1/2 w-80 animate-fade-in" style={{ animationDelay: "0.5s" }}>
          <div className="bg-navy/70 backdrop-blur-md border border-white/15 rounded-2xl p-5">
            <p className="text-primary-foreground/80 text-xs font-body font-medium uppercase tracking-wider mb-4">
              {t("landing.hero.samples")}
            </p>
            <div className="flex flex-col gap-2">
              {sampleQuestions.map((q, i) => (
                <Link
                  key={i}
                  to="/advisor"
                  className="group flex items-start gap-2 p-3 rounded-lg hover:bg-white/8 transition-colors cursor-pointer"
                >
                  <MessageSquare className="w-3.5 h-3.5 text-gold mt-0.5 shrink-0" />
                  <span className="text-primary-foreground/95 text-xs font-body leading-relaxed group-hover:text-primary-foreground transition-colors">
                    {q}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-navy py-14 border-y border-gold/15">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-3 gap-8">
            {stats.map((s, i) => (
              <div key={i} className="text-center">
                <div className="font-display text-3xl md:text-4xl font-bold text-gold mb-1">{s.value}</div>
                <div className="text-primary-foreground/50 text-sm font-body">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 bg-background">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-muted mb-5">
              <Star className="w-3.5 h-3.5 text-gold" />
              <span className="text-accent-foreground text-xs font-body font-medium">{t("landing.features.badge")}</span>
            </div>
            <h2 className="font-display text-4xl md:text-5xl font-bold text-foreground mb-4">
              {t("landing.features.title")}
            </h2>
            <p className="text-muted-foreground font-body text-lg max-w-2xl mx-auto">
              {t("landing.features.sub")}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div
                key={i}
                className="group p-7 rounded-2xl border border-border bg-card hover:border-gold/30 hover:shadow-md transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-gold-muted border border-gold/20 flex items-center justify-center mb-5 group-hover:bg-gold/15 group-hover:border-gold/40 transition-colors">
                  <f.icon className="w-5 h-5 text-gold" />
                </div>
                <h3 className="font-display text-lg font-semibold text-foreground mb-2">{f.title}</h3>
                <p className="text-muted-foreground font-body text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Dashboard Preview */}
      <section className="py-24 bg-cream">
        <div className="container mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-muted mb-6">
                <BookOpen className="w-3.5 h-3.5 text-gold" />
                <span className="text-accent-foreground text-xs font-body font-medium">{t("landing.dash.badge")}</span>
              </div>
              <h2 className="font-display text-4xl font-bold text-foreground mb-6">
                {t("landing.dash.title")}
              </h2>
              <p className="text-muted-foreground font-body text-base leading-relaxed mb-6">
                {t("landing.dash.sub")}
              </p>
              <ul className="space-y-3 mb-8">
                {[
                  t("landing.dash.bullet1"),
                  t("landing.dash.bullet2"),
                  t("landing.dash.bullet3"),
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm font-body text-muted-foreground">
                    <CheckCircle2 className="w-4 h-4 text-gold shrink-0 mt-0.5" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                to="/advisor"
                className="group inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-navy text-primary-foreground font-body font-medium hover:bg-navy-mid transition-colors"
              >
                {t("landing.dash.cta")}
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>

            {/* Browser frame card */}
            <div className="rounded-2xl border border-border bg-card shadow-lg overflow-hidden">
              <div className="bg-muted border-b border-border px-4 py-3 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400/60" />
                  <div className="w-3 h-3 rounded-full bg-amber-400/60" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400/60" />
                </div>
                <div className="flex-1 mx-3">
                  <div className="bg-background rounded px-3 py-0.5 text-xs text-muted-foreground font-body text-center">
                    {t("landing.dash.browserLabel")}
                  </div>
                </div>
              </div>

              <div className="p-5 space-y-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-display text-sm font-semibold text-foreground">{t("landing.dash.dashboardTitle")}</span>
                  <span className="text-xs text-muted-foreground font-body bg-muted px-2 py-0.5 rounded-full">3 {t("advisor.cases")}</span>
                </div>

                {PREVIEW_CASES.map((c, idx) => {
                  const doneSteps = c.steps.filter((s) => s.done).length;
                  const progress = Math.round((doneSteps / c.steps.length) * 100);
                  const status = statusConfig[c.status];

                  return (
                    <div key={idx} className="border border-border rounded-xl p-3.5 bg-background">
                      <div className="flex items-start justify-between gap-2 mb-2.5">
                        <div>
                          <p className="font-body font-semibold text-foreground text-xs leading-snug">{c.titleKey}</p>
                          <p className="text-xs text-muted-foreground font-body mt-0.5">{c.date}</p>
                        </div>
                        <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-body font-medium ${status.className}`}>
                          {status.label}
                        </span>
                      </div>

                      <div className="mb-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-muted-foreground font-body">{doneSteps}/{c.steps.length} {t("case.steps")}</span>
                          <span className="text-xs text-muted-foreground font-body">{progress}%</span>
                        </div>
                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              c.status === "completed" ? "bg-emerald-500" :
                              c.status === "in_progress" ? "bg-blue-500" : "bg-amber-400"
                            }`}
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1 mb-2">
                        {c.steps.map((step, i) => (
                          <span
                            key={i}
                            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-body ${
                              step.done ? "bg-emerald-50 text-emerald-700" : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {step.done
                              ? <CheckCircle2 className="w-2.5 h-2.5" />
                              : <Circle className="w-2.5 h-2.5" />
                            }
                            {step.label}
                          </span>
                        ))}
                      </div>

                      {"deadline" in c && c.status === "in_progress" && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-50 border border-amber-200">
                          <Bell className="w-3 h-3 text-amber-600 shrink-0" />
                          <span className="text-xs font-body text-amber-700">
                            <strong>{t("case.deadline")}:</strong> {(c as typeof c & { deadline: string }).deadline}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Legal areas */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-muted mb-6">
                <Building2 className="w-3.5 h-3.5 text-gold" />
                <span className="text-accent-foreground text-xs font-body font-medium">{t("landing.areas.badge")}</span>
              </div>
              <h2 className="font-display text-4xl font-bold text-foreground mb-6">
                {t("landing.areas.title")}
              </h2>
              <p className="text-muted-foreground font-body text-base leading-relaxed mb-8">
                {t("landing.areas.sub")}
              </p>
              <Link
                to="/advisor"
                className="group inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-navy text-primary-foreground font-body font-medium hover:bg-navy-mid transition-colors"
              >
                {t("landing.areas.cta")}
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {legalAreas.map((item, i) => (
                <div key={i} className="p-4 rounded-xl bg-white border border-border hover:border-gold/30 hover:shadow-sm transition-all">
                  <div className="text-xs font-body font-semibold text-gold mb-1">{item.law}</div>
                  <div className="text-sm font-body text-foreground font-medium">{item.area}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-navy relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full bg-gold blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-64 h-64 rounded-full bg-gold blur-2xl" />
        </div>
        <div className="relative container mx-auto px-6 text-center">
          <Zap className="w-10 h-10 text-gold mx-auto mb-6" />
          <h2 className="font-display text-4xl md:text-5xl font-bold text-primary-foreground mb-5">
            {t("landing.cta.title")}
          </h2>
          <p className="text-primary-foreground/60 font-body text-lg max-w-xl mx-auto mb-10">
            {t("landing.cta.sub")}
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/advisor"
              className="group inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-gold text-accent-foreground font-body font-semibold hover:bg-gold-light transition-all shadow-gold hover:-translate-y-0.5"
            >
              {t("landing.cta.btn1")}
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/permits"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-lg border border-primary-foreground/25 text-primary-foreground font-body font-medium hover:bg-white/8 transition-all"
            >
              {t("landing.cta.btn2")}
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-navy border-t border-gold/15 py-10">
        <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-gold" />
            <span className="font-display font-bold text-primary-foreground">
              Recht<span className="text-gold">Immobilien</span>
            </span>
          </div>
          <p className="text-primary-foreground/40 text-xs font-body text-center">
            {t("landing.footer.disclaimer")}
          </p>
          <p className="text-primary-foreground/30 text-xs font-body">{t("landing.footer.copy")}</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
