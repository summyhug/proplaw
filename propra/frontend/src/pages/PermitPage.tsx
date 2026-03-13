import { useState } from "react";
import { CheckCircle2, Circle, Lock, ChevronRight, Building2, FileText, Search, Users, ClipboardCheck, Hammer, Star, Crown, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { useLanguage } from "@/context/LanguageContext";

interface Step {
  id: number;
  phase: string;
  title: string;
  duration: string;
  authority: string;
  description: string;
  tasks: string[];
  legalBasis: string;
  tips?: string;
}

const PERMIT_STEPS: Step[] = [
  {
    id: 1,
    phase: "Phase 1",
    title: "Initial Property & Zoning Assessment",
    duration: "1–2 weeks",
    authority: "Local Bauamt",
    description: "Before any planning begins, verify what is legally permissible on your plot.",
    tasks: [
      "Request a Bebauungsplan extract from your municipality",
      "Check GRZ (Grundflächenzahl) and GFZ (Geschossflächenzahl) limits",
      "Verify the area classification (Wohngebiet, Mischgebiet, etc.)",
      "Check for Denkmalschutz (heritage protection) status",
      "Review Abstandsflächen (setback) requirements per LBO",
    ],
    legalBasis: "§§ 30–35 BauGB · BauNVO §§ 1–15 · LBO (state-specific)",
    tips: "A preliminary inquiry (Voranfrage) to the Bauamt can clarify feasibility before you invest in full plans.",
  },
  {
    id: 2,
    phase: "Phase 2",
    title: "Engage a Licensed Architect",
    duration: "1–3 weeks",
    authority: "Architektenkammer",
    description: "Appoint a Bauvorlageberechtigter — a licensed architect authorized to submit permit applications.",
    tasks: [
      "Hire an architect registered with the local Architektenkammer",
      "Commission a site survey (Bestandsaufnahme)",
      "Define the project scope in a preliminary design (Vorentwurf)",
      "Discuss structural engineering requirements",
      "Clarify accessibility requirements under LBO (Barrierefreiheit)",
    ],
    legalBasis: "LBO §§ (state-specific) · HOAI 2021 (architect fees)",
    tips: "Architect fees are regulated by the HOAI — expect 10–15% of total construction costs for full services.",
  },
  {
    id: 3,
    phase: "Phase 3",
    title: "Prepare & Submit the Bauantrag",
    duration: "2–4 weeks (preparation)",
    authority: "Bauaufsichtsbehörde",
    description: "Compile the complete permit application package and submit to the building authority.",
    tasks: [
      "Prepare architectural drawings (Bauzeichnungen) at scale 1:100",
      "Complete the official Bauantragsformular",
      "Obtain a certified site plan (Lageplan) from a registered surveyor",
      "Prepare structural calculations (Statik) if required",
      "Compile energy efficiency proof (GEG-Nachweis)",
      "Submit application with all annexes to Bauaufsicht",
    ],
    legalBasis: "BauGB § 72 · LBO Verfahrensvorschriften · GEG 2024",
    tips: "Incomplete applications are the #1 cause of delays. Use the official checklist from your Bauamt.",
  },
  {
    id: 4,
    phase: "Phase 4",
    title: "Authority Review & Neighbors' Notification",
    duration: "4–12 weeks (legally mandated)",
    authority: "Bauaufsicht + Nachbarn",
    description: "The authority reviews your application. Neighboring property owners are formally notified.",
    tasks: [
      "Authorities circulate application to relevant departments (Feuerwehr, Naturschutz, etc.)",
      "Adjacent property owners are notified under LBO Nachbarschutz",
      "Respond promptly to any requests for additional information (Mängelbescheide)",
      "Attend coordination meetings if required",
      "Neighbors have right to object within set deadlines",
    ],
    legalBasis: "LBO Nachbarbeteiligung · VwGO (administrative court procedure)",
    tips: "Proactively inform neighbors before submitting — this often prevents formal objections.",
  },
  {
    id: 5,
    phase: "Phase 5",
    title: "Receive Baugenehmigung",
    duration: "1–2 weeks after approval",
    authority: "Bauaufsichtsbehörde",
    description: "Your permit is issued. Review it carefully before any work begins.",
    tasks: [
      "Carefully read all Nebenbestimmungen (conditions and requirements)",
      "Note the Gültigkeitsdauer (validity period — typically 3 years)",
      "Verify construction must begin within the stated period",
      "Obtain required insurance (Bauleistungsversicherung, Haftpflicht)",
      "Post the permit visibly on-site during construction",
    ],
    legalBasis: "LBO § 68 · BauGB § 74",
    tips: "A Baugenehmigung is typically valid for 3 years. You must begin construction within this period.",
  },
  {
    id: 6,
    phase: "Phase 6",
    title: "Construction & Inspections",
    duration: "Project-dependent",
    authority: "Bauaufsicht + Prüfingenieure",
    description: "Execute the construction in strict accordance with the approved plans.",
    tasks: [
      "Notify Bauaufsicht before construction begins (Baubeginn-Anzeige)",
      "Hire a qualified Bauleiter (site manager) as required by LBO",
      "Schedule mandatory Rohbauabnahme (structural inspection)",
      "Keep a Bautagesbuch (construction diary)",
      "Do not deviate from approved plans without prior amendment (Nachtrag)",
      "Complete all required intermediate inspections",
    ],
    legalBasis: "LBO Bauleitung · DIN standards · VOB/A,B,C",
  },
  {
    id: 7,
    phase: "Phase 7",
    title: "Final Inspection & Bauabnahme",
    duration: "1–4 weeks",
    authority: "Bauaufsichtsbehörde",
    description: "The completed project is formally inspected and approved for use.",
    tasks: [
      "Submit Fertigstellungsanzeige (completion notice) to Bauaufsicht",
      "Schedule Schlussabnahme (final inspection) appointment",
      "Obtain Konformitätsbescheinigung if using certified building components",
      "Receive Baufertigstellungsanzeige confirmation",
      "Update the Grundbuch (land register) if structural changes affect the property record",
    ],
    legalBasis: "LBO § 82 · GBO §§ 19–20",
    tips: "After final inspection, update your property insurance to reflect the new construction.",
  },
];

const PermitPage = () => {
  const { t } = useLanguage();
  const [isMember] = useState(false);
  const [showDemo, setShowDemo] = useState(false);
  const [selectedProject, setSelectedProject] = useState("extension");
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [activeStep, setActiveStep] = useState<number | null>(1);

  const PROJECT_TYPES = [
    { id: "extension", label: t("permit.proj.extension"), icon: Building2 },
    { id: "renovation", label: t("permit.proj.renovation"), icon: Hammer },
    { id: "newbuild", label: t("permit.proj.newbuild"), icon: Building2 },
    { id: "conversion", label: t("permit.proj.conversion"), icon: FileText },
  ];

  const toggleStep = (id: number) => {
    setCompletedSteps((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const progress = Math.round((completedSteps.length / PERMIT_STEPS.length) * 100);

  if (!showDemo && !isMember) {
    return (
      <div className="min-h-screen bg-background pt-16">
        <div className="container mx-auto px-6 py-20 max-w-5xl">
          {/* Hero */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-muted mb-6">
              <Crown className="w-3.5 h-3.5 text-gold" />
              <span className="text-accent-foreground text-xs font-body font-medium">{t("permit.badge")}</span>
            </div>
            <h1 className="font-display text-5xl font-bold text-foreground mb-5">
              {t("permit.title1")}
              <br />
              <span className="text-gold">{t("permit.title2")}</span>
            </h1>
            <p className="text-muted-foreground font-body text-xl max-w-2xl mx-auto leading-relaxed">
              {t("permit.sub")}
            </p>
          </div>

          {/* Features preview */}
          <div className="grid md:grid-cols-3 gap-6 mb-14">
            {[
              { icon: ClipboardCheck, title: t("permit.feat1.title"), desc: t("permit.feat1.desc") },
              { icon: FileText, title: t("permit.feat2.title"), desc: t("permit.feat2.desc") },
              { icon: Users, title: t("permit.feat3.title"), desc: t("permit.feat3.desc") },
            ].map((f, i) => (
              <div key={i} className="p-6 rounded-2xl border border-border bg-card text-center">
                <div className="w-12 h-12 rounded-xl bg-gold-muted border border-gold/20 flex items-center justify-center mx-auto mb-4">
                  <f.icon className="w-5 h-5 text-gold" />
                </div>
                <h3 className="font-display font-semibold text-foreground mb-2">{f.title}</h3>
                <p className="text-muted-foreground text-sm font-body">{f.desc}</p>
              </div>
            ))}
          </div>

          {/* Preview teaser */}
          <div className="relative mb-14">
            <div className="rounded-2xl border border-border bg-card overflow-hidden">
              <div className="bg-navy px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Building2 className="w-5 h-5 text-gold" />
                  <span className="text-primary-foreground font-display font-semibold">{t("permit.header.title")}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-400" />
                  <div className="w-2 h-2 rounded-full bg-yellow-400" />
                  <div className="w-2 h-2 rounded-full bg-green-400" />
                </div>
              </div>
              <div className="p-6 space-y-3">
                {PERMIT_STEPS.slice(0, 3).map((step) => (
                  <div key={step.id} className="flex items-center gap-4 p-3 rounded-xl bg-muted/50 opacity-80">
                    <div className="w-8 h-8 rounded-full border-2 border-gold/40 flex items-center justify-center">
                      <span className="text-gold text-xs font-bold">{step.id}</span>
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-foreground font-body">{step.title}</div>
                      <div className="text-xs text-muted-foreground font-body">{step.authority} · {step.duration}</div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </div>
                ))}
                <div className="flex items-center gap-4 p-3 rounded-xl bg-muted/50 opacity-50 blur-[1px]">
                  <div className="w-8 h-8 rounded-full border-2 border-border flex items-center justify-center">
                    <Lock className="w-3.5 h-3.5 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-muted-foreground font-body">{t("permit.locked")}</div>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent flex items-end justify-center pb-8">
              <div className="text-center">
                <Lock className="w-8 h-8 text-gold mx-auto mb-3" />
                <p className="text-muted-foreground font-body text-sm mb-4">{t("permit.unlock")}</p>
                <button
                  onClick={() => setShowDemo(true)}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-navy text-primary-foreground font-body font-semibold hover:bg-navy-mid transition-all shadow-md"
                >
                  <Star className="w-4 h-4 text-gold" />
                  {t("permit.demo")}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Pricing CTA */}
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {[
              {
                name: t("permit.plan1.name"),
                price: t("permit.plan1.price"),
                desc: t("permit.plan1.desc"),
                features: [t("permit.plan1.f1"), t("permit.plan1.f2"), t("permit.plan1.f3")],
                cta: t("permit.plan1.cta"),
                highlight: false,
              },
              {
                name: t("permit.plan2.name"),
                price: t("permit.plan2.price"),
                desc: t("permit.plan2.desc"),
                features: [t("permit.plan2.f1"), t("permit.plan2.f2"), t("permit.plan2.f3"), t("permit.plan2.f4"), t("permit.plan2.f5")],
                cta: t("permit.plan2.cta"),
                highlight: true,
              },
            ].map((plan, i) => (
              <div
                key={i}
                className={`p-7 rounded-2xl border ${plan.highlight ? "border-gold bg-navy text-primary-foreground" : "border-border bg-card"}`}
              >
                {plan.highlight && (
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gold/20 border border-gold/30 mb-4">
                    <Star className="w-3 h-3 text-gold" />
                    <span className="text-gold text-xs font-body font-medium">{t("permit.popular")}</span>
                  </div>
                )}
                <div className="font-display text-2xl font-bold mb-1">{plan.price}</div>
                <div className={`text-sm font-body font-semibold mb-1 ${plan.highlight ? "text-gold" : "text-foreground"}`}>{plan.name}</div>
                <div className={`text-sm font-body mb-5 ${plan.highlight ? "text-primary-foreground/60" : "text-muted-foreground"}`}>{plan.desc}</div>
                <ul className="space-y-2 mb-6">
                  {plan.features.map((f, j) => (
                    <li key={j} className="flex items-center gap-2 text-sm font-body">
                      <CheckCircle2 className={`w-4 h-4 ${plan.highlight ? "text-gold" : "text-emerald-500"}`} />
                      <span className={plan.highlight ? "text-primary-foreground/80" : "text-foreground/80"}>{f}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => plan.highlight && setShowDemo(true)}
                  className={`w-full py-3 rounded-xl font-body font-semibold text-sm transition-all ${
                    plan.highlight
                      ? "bg-gold text-accent-foreground hover:bg-gold-light shadow-gold"
                      : "border border-border bg-transparent hover:bg-muted text-foreground"
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Full permit process (demo / members)
  return (
    <div className="min-h-screen bg-background pt-16">
      <div className="container mx-auto px-4 max-w-5xl py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Crown className="w-4 h-4 text-gold" />
              <span className="text-gold text-xs font-body font-semibold uppercase tracking-wide">{t("permit.badge")}</span>
            </div>
            <h1 className="font-display text-3xl font-bold text-foreground">{t("permit.wizard.title")}</h1>
            <p className="text-muted-foreground font-body text-sm mt-1">{t("permit.wizard.sub")}</p>
          </div>
          <div className="sm:ml-auto flex flex-col items-end gap-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-body text-muted-foreground">{completedSteps.length}/{PERMIT_STEPS.length} {t("permit.wizard.steps")}</span>
              <span className="text-sm font-semibold font-body text-foreground">{progress}%</span>
            </div>
            <div className="w-48 h-2 rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-gold transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Project type selector */}
        <div className="flex flex-wrap gap-2 mb-8">
          {PROJECT_TYPES.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelectedProject(p.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-body font-medium transition-all ${
                selectedProject === p.id
                  ? "bg-navy border-navy text-primary-foreground"
                  : "border-border bg-card text-muted-foreground hover:border-gold/40 hover:text-foreground"
              }`}
            >
              <p.icon className="w-3.5 h-3.5" />
              {p.label}
            </button>
          ))}
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {PERMIT_STEPS.map((step) => {
            const isCompleted = completedSteps.includes(step.id);
            const isActive = activeStep === step.id;

            return (
              <div
                key={step.id}
                className={`rounded-2xl border transition-all duration-300 overflow-hidden ${
                  isCompleted
                    ? "border-emerald-200 bg-emerald-50/50"
                    : isActive
                    ? "border-gold/40 bg-card shadow-md"
                    : "border-border bg-card"
                }`}
              >
                {/* Step header */}
                <button
                  onClick={() => setActiveStep(isActive ? null : step.id)}
                  className="w-full flex items-center gap-4 p-5 text-left hover:bg-muted/30 transition-colors"
                >
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleStep(step.id); }}
                    className="shrink-0"
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="w-7 h-7 text-emerald-500" />
                    ) : (
                      <Circle className={`w-7 h-7 ${isActive ? "text-gold" : "text-muted-foreground/40"}`} />
                    )}
                  </button>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-body font-semibold text-gold uppercase tracking-wide">{step.phase}</span>
                      <span className="text-xs text-muted-foreground font-body">· {step.duration}</span>
                    </div>
                    <div className={`font-display font-semibold text-base ${isCompleted ? "line-through text-muted-foreground" : "text-foreground"}`}>
                      {step.title}
                    </div>
                    <div className="text-xs text-muted-foreground font-body mt-0.5">{step.authority}</div>
                  </div>

                  <div className={`transition-transform shrink-0 ${isActive ? "rotate-90" : ""}`}>
                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                  </div>
                </button>

                {/* Expanded content */}
                {isActive && (
                  <div className="px-5 pb-5 border-t border-border">
                    <p className="text-sm font-body text-muted-foreground mt-4 mb-4 leading-relaxed">
                      {step.description}
                    </p>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <ClipboardCheck className="w-4 h-4 text-gold" />
                          <span className="text-xs font-body font-semibold uppercase tracking-wide text-foreground">{t("permit.step.tasks")}</span>
                        </div>
                        <ul className="space-y-2">
                          {step.tasks.map((task, i) => (
                            <li key={i} className="flex items-start gap-2.5">
                              <div className="w-4 h-4 rounded border border-border flex items-center justify-center mt-0.5 shrink-0 bg-muted/50">
                                <div className="w-1.5 h-1.5 rounded-full bg-gold/40" />
                              </div>
                              <span className="text-sm font-body text-foreground/80 leading-relaxed">{task}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="space-y-4">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Search className="w-4 h-4 text-gold" />
                            <span className="text-xs font-body font-semibold uppercase tracking-wide text-foreground">{t("permit.step.legal")}</span>
                          </div>
                          <div className="p-3 rounded-xl bg-navy/8 border border-gold/20">
                            <p className="text-xs font-body font-medium text-gold">{step.legalBasis}</p>
                          </div>
                        </div>

                        {step.tips && (
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <Star className="w-4 h-4 text-gold" />
                              <span className="text-xs font-body font-semibold uppercase tracking-wide text-foreground">{t("permit.step.tip")}</span>
                            </div>
                            <div className="p-3 rounded-xl bg-gold-muted border border-gold/20">
                              <p className="text-xs font-body text-accent-foreground leading-relaxed">{step.tips}</p>
                            </div>
                          </div>
                        )}

                        <button
                          onClick={() => toggleStep(step.id)}
                          className={`w-full py-2.5 rounded-xl border text-sm font-body font-medium transition-all ${
                            isCompleted
                              ? "border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                              : "border-gold bg-gold-muted text-accent-foreground hover:bg-gold/20"
                          }`}
                        >
                          {isCompleted ? t("permit.step.incomplete") : t("permit.step.complete")}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* CTA at bottom */}
        <div className="mt-10 p-6 rounded-2xl bg-navy border border-gold/20 text-center">
          <p className="text-primary-foreground/70 font-body text-sm mb-3">
            {t("permit.cta.question")}
          </p>
          <Link
            to="/advisor"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gold text-accent-foreground font-body font-semibold text-sm hover:bg-gold-light transition-colors shadow-gold"
          >
            {t("permit.cta.btn")}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default PermitPage;
