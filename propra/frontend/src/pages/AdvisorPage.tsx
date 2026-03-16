import { useState, useRef, useEffect } from "react";
import {
  Send, Scale, BookOpen, Shield, ChevronDown, ChevronUp, Copy,
  ThumbsUp, ThumbsDown, Loader2, FileSignature, Bell,
  CheckCircle2, Circle, Search, Check, Building2, MapPin, Layers, Tag, Home, Trees,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useLanguage } from "@/context/LanguageContext";

const BUNDESLAENDER = [
  "Baden-Württemberg",
  "Bayern",
  "Berlin",
  "Brandenburg",
  "Bremen",
  "Hamburg",
  "Hessen",
  "Mecklenburg-Vorpommern",
  "Niedersachsen",
  "Nordrhein-Westfalen",
  "Rheinland-Pfalz",
  "Saarland",
  "Sachsen",
  "Sachsen-Anhalt",
  "Schleswig-Holstein",
  "Thüringen",
];

interface Source {
  code: string;
  section: string;
  title: string;
  excerpt: string;
  url?: string;
}


interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  reliability?: number;
  reliabilityLabel?: string;
  timestamp: Date;
  documentBlock?: string;
  classificationLabel?: string;
  awaitingClassification?: boolean;
}

interface CaseStep {
  label: string;
  done: boolean;
}

interface Case {
  id: number;
  title: string;
  status: "in_progress" | "completed" | "pending";
  date: string;
  deadline?: string;
  steps: CaseStep[];
}


const CASES: Case[] = [
  {
    id: 1,
    title: "Widerspruch gegen Baugenehmigung Nachbar",
    status: "in_progress",
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
    id: 2,
    title: "Eigenbedarfskündigung – Rechtslage prüfen",
    status: "completed",
    date: "08.01.2024",
    steps: [
      { label: "Rechtslage analysiert", done: true },
      { label: "Widerspruch formuliert", done: true },
      { label: "Einigung erzielt", done: true },
    ],
  },
  {
    id: 3,
    title: "Grunderwerbsteuer-Einspruch vorbereiten",
    status: "pending",
    date: "28.02.2024",
    steps: [
      { label: "Unterlagen zusammenstellen", done: false },
      { label: "Einspruch einreichen", done: false },
      { label: "Finanzamt-Antwort abwarten", done: false },
    ],
  },
];

const LOADING_MESSAGES = [
  "Wir prüfen die Vorschriften für Ihre Region...",
  "Rechtliche Quellen werden durchsucht...",
  "Antwort wird zusammengestellt...",
];
const LOADING_TIMEOUT_MSG = "Das dauert länger als erwartet. Bitte warten...";

const classifyQuestion = (text: string): string | null => {
  const lower = text.toLowerCase();
  if (["zaun", "grenze", "hecke"].some((k) => lower.includes(k))) return "Zaun / Grenze";
  if (["fenster", "öffnung", "tür"].some((k) => lower.includes(k))) return "Fenster / Öffnung";
  if (["garten", "terrasse", "schuppen"].some((k) => lower.includes(k))) return "Gartenanlage";
  return null;
};

const CLASSIFICATION_TILES = ["Zaun / Grenze", "Fenster / Öffnung", "Gartenanlage"];

const ReliabilityBadge = ({ score, label }: { score: number; label: string }) => {
  const color =
    score >= 90 ? "text-emerald-700 bg-emerald-50 border-emerald-200" :
    score >= 75 ? "text-blue-700 bg-blue-50 border-blue-200" :
    "text-amber-700 bg-amber-50 border-amber-200";

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-body font-medium ${color}`}>
      <Shield className="w-3 h-3" />
      {label} — {score}% confidence
    </div>
  );
};

const SourceCard = ({ source, index }: { source: Source; index: number }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-border rounded-xl overflow-hidden bg-cream hover:border-gold/30 transition-colors">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-gold-muted/30 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-navy flex items-center justify-center shrink-0">
            <span className="text-primary-foreground text-xs font-body font-bold">{index + 1}</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-body font-bold text-gold">{source.code}</span>
              <span className="text-xs font-body font-semibold text-foreground">{source.section}</span>
            </div>
            <div className="text-xs text-muted-foreground font-body">{source.title}</div>
          </div>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
      </button>
      {expanded && (
        <div className="px-4 pb-3 pt-0 border-t border-border">
          <p className="text-xs font-body text-muted-foreground italic leading-relaxed mt-2">
            "{source.excerpt}"
          </p>
        </div>
      )}
    </div>
  );
};

const DocumentCard = ({ content, title, copyLabel, copiedLabel, wordsLabel }: {
  content: string;
  title: string;
  copyLabel: string;
  copiedLabel: string;
  wordsLabel: string;
}) => {
  const [copied, setCopied] = useState(false);
  const wordCount = content.trim().split(/\s+/).length;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-4 border border-gold/30 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-gold/20 bg-gold-muted/30">
        <div className="flex items-center gap-2">
          <FileSignature className="w-4 h-4 text-gold" />
          <span className="text-xs font-body font-semibold text-foreground">Entwurf: {title}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground font-body">{wordCount} {wordsLabel}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gold/15 hover:bg-gold/25 text-gold text-xs font-body font-medium transition-colors"
          >
            <Copy className="w-3 h-3" />
            {copied ? copiedLabel : copyLabel}
          </button>
        </div>
      </div>
      <div className="p-4 max-h-64 overflow-y-auto bg-cream/50">
        <pre className="text-xs font-mono text-foreground/80 whitespace-pre-wrap leading-relaxed">{content}</pre>
      </div>
    </div>
  );
};

const CaseCard = ({ case: c, statusConfig, stepsLabel, deadlineLabel }: {
  case: Case;
  statusConfig: Record<string, { label: string; className: string }>;
  stepsLabel: string;
  deadlineLabel: string;
}) => {
  const doneSteps = c.steps.filter((s) => s.done).length;
  const progress = Math.round((doneSteps / c.steps.length) * 100);
  const status = statusConfig[c.status];

  return (
    <div className="border border-border rounded-xl p-4 bg-background hover:border-gold/30 hover:shadow-sm transition-all">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="font-body font-semibold text-foreground text-sm">{c.title}</h3>
          <p className="text-xs text-muted-foreground font-body mt-0.5">{c.date}</p>
        </div>
        <span className={`shrink-0 inline-flex items-center px-2.5 py-1 rounded-full border text-xs font-body font-medium ${status.className}`}>
          {status.label}
        </span>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted-foreground font-body">{doneSteps}/{c.steps.length} {stepsLabel}</span>
          <span className="text-xs text-muted-foreground font-body">{progress}%</span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              c.status === "completed" ? "bg-emerald-500" :
              c.status === "in_progress" ? "bg-blue-500" : "bg-amber-400"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {c.steps.map((step, i) => (
          <span
            key={i}
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-body ${
              step.done ? "bg-emerald-50 text-emerald-700" : "bg-muted text-muted-foreground"
            }`}
          >
            {step.done ? <CheckCircle2 className="w-3 h-3" /> : <Circle className="w-3 h-3" />}
            {step.label}
          </span>
        ))}
      </div>

      {c.deadline && c.status === "in_progress" && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200">
          <Bell className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span className="text-xs font-body text-amber-700">
            <strong>{deadlineLabel}:</strong> {c.deadline} — Widerspruch muss eingereicht sein
          </span>
        </div>
      )}
    </div>
  );
};

const LoadingMessage = () => {
  const [msgIndex, setMsgIndex] = useState(0);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    const cycleInterval = setInterval(() => {
      setMsgIndex((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 3000);
    const timeoutTimer = setTimeout(() => setTimedOut(true), 15000);
    return () => {
      clearInterval(cycleInterval);
      clearTimeout(timeoutTimer);
    };
  }, []);

  return (
    <div className="flex gap-4 animate-fade-in">
      <div className="w-9 h-9 rounded-xl bg-navy border border-gold/30 flex items-center justify-center shrink-0 mt-1">
        <Scale className="w-4 h-4 text-gold" />
      </div>
      <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-3">
        <Loader2 className="w-4 h-4 text-gold animate-spin shrink-0" />
        <span className="text-sm text-muted-foreground font-body">
          {timedOut ? LOADING_TIMEOUT_MSG : LOADING_MESSAGES[msgIndex]}
        </span>
      </div>
    </div>
  );
};

const AdvisorPage = () => {
  const { t } = useLanguage();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"berater" | "vorgaenge">("berater");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const bundeslandRef = useRef<HTMLDivElement>(null);

  // Guided context inputs
  const [bundesland, setBundesland] = useState("");
  const [bundeslandSearch, setBundeslandSearch] = useState("");
  const [bundeslandOpen, setBundeslandOpen] = useState(false);
  const [propertyType, setPropertyType] = useState("");
  const [insideOutside, setInsideOutside] = useState<"inside" | "outside" | "">("");
  const [postcode, setPostcode] = useState("");
  const [floors, setFloors] = useState("");

  const contextReady =
    bundesland !== "" &&
    propertyType !== "" &&
    insideOutside !== "" &&
    (insideOutside !== "inside" || (floors !== "" && Number(floors) > 0));

  // Close Bundesland dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (bundeslandRef.current && !bundeslandRef.current.contains(e.target as Node)) {
        setBundeslandOpen(false);
      }
    };
    if (bundeslandOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [bundeslandOpen]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const statusConfig = {
    in_progress: { label: t("status.in_progress"), className: "bg-blue-50 text-blue-700 border-blue-200" },
    completed: { label: t("status.completed"), className: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    pending: { label: t("status.pending"), className: "bg-amber-50 text-amber-700 border-amber-200" },
  };

  const sendMessage = async (text?: string) => {
    const question = text || input.trim();
    if (!question || loading) return;

    const userMsg: Message = {
      id: Date.now(),
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // TODO: replace with Render URL once Sebastian confirms endpoint
      const res = await fetch("https://proplaw-api.onrender.com/api/assess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jurisdiction: bundesland,
          property_type: propertyType,
          language: "de",
          floors: floors ? Number(floors) : null,
          inside_outside: insideOutside,
          postcode,
          project_description: question,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();

      const confidenceScore =
        data.confidence === "HIGH" ? 90 :
        data.confidence === "MEDIUM" ? 70 : 50;

      const sources: Source[] = (data.citations ?? []).map(
        (c: { regulation_name: string; paragraph: string; jurisdiction: string; text: string }) => ({
          code: c.regulation_name,
          section: c.paragraph,
          title: c.jurisdiction,
          excerpt: c.text,
        })
      );

      const nextActionsText = data.next_actions?.length
        ? "\n\n**Nächste Schritte:**\n" + data.next_actions.map((a: string) => `- ${a}`).join("\n")
        : "";
      const content = `**${data.verdict}**\n\n${data.explanation}${nextActionsText}`;

      const label = classifyQuestion(question);
      const aiMsg: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content,
        sources,
        reliability: confidenceScore,
        reliabilityLabel: data.confidence_note ?? data.confidence,
        timestamp: new Date(),
        classificationLabel: label ?? undefined,
        awaitingClassification: label === null,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      const errMsg: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content: "Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const setMessageClassification = (id: number, label: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, classificationLabel: label, awaitingClassification: false } : m
      )
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const renderContent = (text: string) => {
    return text.split("\n").map((line, i) => {
      if (line.startsWith("**") && line.endsWith("**")) {
        return <p key={i} className="font-semibold text-foreground mt-3 mb-1 first:mt-0">{line.slice(2, -2)}</p>;
      }
      if (line.startsWith("- ")) {
        return <li key={i} className="ml-4 text-foreground/85">{line.slice(2)}</li>;
      }
      if (line.trim() === "") return <br key={i} />;
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      return (
        <p key={i} className="text-foreground/85 leading-relaxed">
          {parts.map((p, j) =>
            p.startsWith("**") && p.endsWith("**")
              ? <strong key={j} className="font-semibold text-foreground">{p.slice(2, -2)}</strong>
              : p
          )}
        </p>
      );
    });
  };

  return (
    <div className="min-h-screen bg-background pt-16 flex flex-col">
      <div className="container mx-auto px-4 max-w-4xl flex-1 flex flex-col py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <div className="w-11 h-11 rounded-xl bg-navy border border-gold/30 flex items-center justify-center shadow-md">
            <Scale className="w-5 h-5 text-gold" />
          </div>
          <div>
            <h1 className="font-display text-2xl font-bold text-foreground">{t("advisor.title")}</h1>
            <p className="text-muted-foreground text-sm font-body">{t("advisor.sub")}</p>
          </div>
          <div className="ml-auto hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-emerald-700 text-xs font-body font-medium">{t("advisor.online")}</span>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "berater" | "vorgaenge")} className="flex-1 flex flex-col">
          <TabsList className="mb-5 self-start bg-muted">
            <TabsTrigger value="berater" className="font-body text-sm gap-2">
              <Scale className="w-3.5 h-3.5" />
              {t("advisor.tab.advisor")}
            </TabsTrigger>
            <TabsTrigger value="vorgaenge" className="font-body text-sm gap-2">
              <BookOpen className="w-3.5 h-3.5" />
              {t("advisor.tab.cases")}
            </TabsTrigger>
          </TabsList>

          {/* ── Tab 1: AI Advisor ── */}
          <TabsContent value="berater" className="flex-1 flex flex-col mt-0">
            {/* Greeting */}
            <div className="flex gap-4 mb-5 animate-fade-up">
              <div className="w-9 h-9 rounded-xl bg-navy border border-gold/30 flex items-center justify-center shrink-0 mt-1">
                <Scale className="w-4 h-4 text-gold" />
              </div>
              <div className="max-w-[85%]">
                <div className="bg-card border border-border rounded-2xl rounded-tl-sm p-5 shadow-sm">
                  <p className="font-body text-sm leading-relaxed">{t("advisor.greeting")}</p>
                </div>
              </div>
            </div>

            {/* Guided context inputs */}
            <div className={`mb-5 border rounded-2xl transition-all ${contextReady ? "border-gold/40 bg-gold-muted/10" : "border-border bg-card"}`}>
              <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
                <Building2 className="w-4 h-4 text-gold shrink-0" />
                <div>
                  <p className="text-sm font-body font-semibold text-foreground">{t("advisor.context.title")}</p>
                  <p className="text-xs text-muted-foreground font-body">{t("advisor.context.sub")}</p>
                </div>
                {contextReady && (
                  <span className="ml-auto flex items-center gap-1.5 text-xs font-body font-medium text-gold">
                    <Check className="w-3.5 h-3.5" />
                    {t("advisor.context.ready")}
                  </span>
                )}
              </div>

              <div className="p-4 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* 1 — Bundesland searchable dropdown */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                    <MapPin className="w-3 h-3 text-gold" />
                    {t("advisor.context.bundesland.label")}
                  </label>
                  <div className="relative" ref={bundeslandRef}>
                    <button
                      type="button"
                      onClick={() => { setBundeslandOpen((o) => !o); if (!bundeslandOpen) setBundeslandSearch(""); }}
                      className={`w-full flex items-center justify-between h-10 px-3 rounded-xl border text-sm font-body transition-colors ${
                        bundesland
                          ? "border-gold/40 bg-gold-muted/10 text-foreground"
                          : "border-border bg-background text-muted-foreground"
                      } hover:border-gold/50`}
                    >
                      <span className="truncate">{bundesland || t("advisor.context.bundesland.placeholder")}</span>
                      <ChevronDown className={`w-4 h-4 shrink-0 ml-2 transition-transform ${bundeslandOpen ? "rotate-180" : ""}`} />
                    </button>
                    {bundeslandOpen && (
                      <div className="absolute z-50 mt-1 w-full bg-popover border border-border rounded-xl shadow-lg overflow-hidden">
                        <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
                          <Search className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                          <input
                            value={bundeslandSearch}
                            onChange={(e) => setBundeslandSearch(e.target.value)}
                            placeholder={t("advisor.context.bundesland.placeholder")}
                            className="flex-1 text-sm font-body bg-transparent outline-none text-foreground placeholder:text-muted-foreground"
                          />
                        </div>
                        <div className="max-h-48 overflow-y-auto py-1">
                          {BUNDESLAENDER
                            .filter((bl) => bl.toLowerCase().includes(bundeslandSearch.toLowerCase()))
                            .map((bl) => (
                              <button
                                key={bl}
                                type="button"
                                onClick={() => { setBundesland(bl); setBundeslandOpen(false); }}
                                className={`w-full text-left px-3 py-2 text-sm font-body hover:bg-accent hover:text-accent-foreground transition-colors flex items-center justify-between ${bundesland === bl ? "text-gold font-medium" : "text-foreground"}`}
                              >
                                {bl}
                                {bundesland === bl && <Check className="w-3.5 h-3.5 text-gold" />}
                              </button>
                            ))
                          }
                          {BUNDESLAENDER.filter((bl) => bl.toLowerCase().includes(bundeslandSearch.toLowerCase())).length === 0 && (
                            <p className="px-3 py-4 text-xs text-muted-foreground font-body text-center">{t("advisor.context.bundesland.empty")}</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* 2 — Property type dropdown */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                    <Building2 className="w-3 h-3 text-gold" />
                    {t("advisor.context.proptype.label")}
                  </label>
                  <div className="relative group">
                    <select
                      value={propertyType}
                      onChange={(e) => setPropertyType(e.target.value)}
                      className={`w-full h-10 px-3 rounded-xl border text-sm font-body appearance-none cursor-pointer transition-colors pr-8 ${
                        propertyType
                          ? "border-gold/40 bg-gold-muted/10 text-foreground"
                          : "border-border bg-background text-muted-foreground"
                      } hover:border-gold/50 focus:outline-none focus:border-gold/50`}
                    >
                      <option value="" disabled>{t("advisor.context.proptype.placeholder")}</option>
                      <option value="einfamilienhaus">{t("advisor.context.proptype.einfamilienhaus")}</option>
                      <option value="mehrfamilienhaus">{t("advisor.context.proptype.mehrfamilienhaus")}</option>
                      <option value="gewerbe">{t("advisor.context.proptype.gewerbe")}</option>
                      <option value="gemischte">{t("advisor.context.proptype.gemischte")}</option>
                      <option value="sonderbau">{t("advisor.context.proptype.sonderbau")}</option>
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
                  </div>
                </div>

                {/* 3 — Inside / Outside tiles */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                    <Home className="w-3 h-3 text-gold" />
                    {t("advisor.context.insideoutside.label")}
                  </label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => { setInsideOutside("inside"); setFloors(""); }}
                      className={`flex-1 flex items-center justify-center gap-1.5 h-10 rounded-xl border text-sm font-body transition-colors ${
                        insideOutside === "inside"
                          ? "border-gold/50 bg-gold-muted/20 text-foreground font-medium"
                          : "border-border bg-background text-muted-foreground hover:border-gold/40"
                      }`}
                    >
                      <Home className="w-3.5 h-3.5" />
                      {t("advisor.context.insideoutside.inside")}
                    </button>
                    <button
                      type="button"
                      onClick={() => { setInsideOutside("outside"); setFloors(""); }}
                      className={`flex-1 flex items-center justify-center gap-1.5 h-10 rounded-xl border text-sm font-body transition-colors ${
                        insideOutside === "outside"
                          ? "border-gold/50 bg-gold-muted/20 text-foreground font-medium"
                          : "border-border bg-background text-muted-foreground hover:border-gold/40"
                      }`}
                    >
                      <Trees className="w-3.5 h-3.5" />
                      {t("advisor.context.insideoutside.outside")}
                    </button>
                  </div>
                </div>
              </div>

              {/* Row 2 — Postcode (always) + Floors (only when inside) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                    <MapPin className="w-3 h-3 text-gold" />
                    {t("advisor.context.postcode.label")}
                  </label>
                  <input
                    type="text"
                    inputMode="numeric"
                    maxLength={5}
                    value={postcode}
                    onChange={(e) => setPostcode(e.target.value.replace(/\D/g, ""))}
                    placeholder={t("advisor.context.postcode.placeholder")}
                    className={`h-10 w-full px-3 rounded-xl border text-sm font-body transition-colors ${
                      postcode
                        ? "border-gold/40 bg-gold-muted/10 text-foreground"
                        : "border-border bg-background text-muted-foreground"
                    } hover:border-gold/50 focus:outline-none focus:border-gold/50`}
                  />
                </div>

                {insideOutside === "inside" && (
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-body font-semibold text-foreground flex items-center gap-1.5">
                      <Layers className="w-3 h-3 text-gold" />
                      {t("advisor.context.floors.label")}
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={99}
                      value={floors}
                      onChange={(e) => setFloors(e.target.value)}
                      placeholder={t("advisor.context.floors.placeholder")}
                      className={`h-10 w-full px-3 rounded-xl border text-sm font-body transition-colors ${
                        floors && Number(floors) > 0
                          ? "border-gold/40 bg-gold-muted/10 text-foreground"
                          : "border-border bg-background text-muted-foreground"
                      } hover:border-gold/50 focus:outline-none focus:border-gold/50 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none`}
                    />
                  </div>
                )}
              </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-6 mb-6 min-h-0 max-h-[60vh] pr-1">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""} animate-fade-up`}>
                  {msg.role === "assistant" && (
                    <div className="w-9 h-9 rounded-xl bg-navy border border-gold/30 flex items-center justify-center shrink-0 mt-1">
                      <Scale className="w-4 h-4 text-gold" />
                    </div>
                  )}

                  <div className={`max-w-[85%] ${msg.role === "user" ? "max-w-[75%]" : ""}`}>
                    {msg.role === "user" ? (
                      <div className="bg-navy text-primary-foreground rounded-2xl rounded-tr-sm px-5 py-3 font-body text-sm leading-relaxed">
                        {msg.content}
                      </div>
                    ) : (
                      <>
                      {msg.classificationLabel && (
                        <div className="mb-1.5">
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-body font-medium bg-navy/10 text-navy border border-navy/20">
                            <Tag className="w-3 h-3" />
                            {msg.classificationLabel}
                          </span>
                        </div>
                      )}
                      <div className="bg-card border border-border rounded-2xl rounded-tl-sm p-5 shadow-sm">
                        <div className="font-body text-sm space-y-1">
                          {renderContent(msg.content)}
                        </div>

                        {msg.documentBlock && (
                          <DocumentCard
                            content={msg.documentBlock}
                            title={msg.documentBlock.includes("Stellungnahme") ? "Stellungnahme" : "Widerspruchsschreiben"}
                            copyLabel={t("advisor.copy")}
                            copiedLabel={t("advisor.copied")}
                            wordsLabel={t("advisor.words")}
                          />
                        )}

                        {msg.reliability && (
                          <div className="mt-4 pt-4 border-t border-border">
                            <ReliabilityBadge score={msg.reliability} label={msg.reliabilityLabel!} />
                          </div>
                        )}

                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-4">
                            <div className="flex items-center gap-2 mb-3">
                              <BookOpen className="w-3.5 h-3.5 text-gold" />
                              <span className="text-xs font-body font-semibold text-foreground uppercase tracking-wide">
                                {t("advisor.sources")} ({msg.sources.length})
                              </span>
                            </div>
                            <div className="space-y-2">
                              {msg.sources.map((source, i) => (
                                <SourceCard key={i} source={source} index={i} />
                              ))}
                            </div>
                          </div>
                        )}

                        {msg.sources && (
                          <div className="mt-4 flex items-center gap-3">
                            <span className="text-xs text-muted-foreground font-body">{t("advisor.helpful")}</span>
                            <button className="p-1.5 rounded-lg hover:bg-muted transition-colors">
                              <ThumbsUp className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                            </button>
                            <button className="p-1.5 rounded-lg hover:bg-muted transition-colors">
                              <ThumbsDown className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                            </button>
                            <button className="p-1.5 rounded-lg hover:bg-muted transition-colors ml-auto">
                              <Copy className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
                            </button>
                          </div>
                        )}

                        {msg.awaitingClassification && (
                          <div className="mt-4 pt-4 border-t border-border">
                            <p className="text-xs font-body text-muted-foreground mb-2">{t("advisor.classify.pick")}</p>
                            <div className="flex flex-wrap gap-2">
                              {CLASSIFICATION_TILES.map((tile) => (
                                <button
                                  key={tile}
                                  type="button"
                                  onClick={() => setMessageClassification(msg.id, tile)}
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-navy/30 bg-navy/5 text-navy text-xs font-body font-medium hover:bg-navy/10 hover:border-navy/50 transition-colors"
                                >
                                  <Tag className="w-3 h-3" />
                                  {tile}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      </>
                    )}
                    <div className="text-xs text-muted-foreground font-body mt-1.5 px-1">
                      {msg.timestamp.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                </div>
              ))}

              {loading && (
                <LoadingMessage />
              )}

              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className={`bg-card border rounded-2xl shadow-md p-3 transition-colors ${!contextReady ? "opacity-60 border-border" : "border-border"}`}>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value.slice(0, 500))}
                onKeyDown={handleKeyDown}
                placeholder={contextReady ? t("advisor.placeholder") : t("advisor.context.sub")}
                rows={3}
                disabled={!contextReady}
                className="w-full bg-transparent font-body text-sm text-foreground placeholder:text-muted-foreground resize-none outline-none leading-relaxed disabled:cursor-not-allowed"
              />
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-border">
                <p className="text-xs text-muted-foreground font-body">
                  {t("advisor.hint")}
                </p>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-body tabular-nums ${
                    input.length > 500 ? "text-red-500" :
                    input.length > 0 && input.trim().length < 10 ? "text-amber-500" :
                    "text-muted-foreground"
                  }`}>
                    {input.length}/500
                  </span>
                  <button
                    onClick={() => sendMessage()}
                    disabled={input.trim().length < 10 || loading || !contextReady}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-navy text-primary-foreground font-body text-sm font-medium disabled:opacity-40 hover:bg-navy-mid transition-colors disabled:cursor-not-allowed"
                  >
                    <Send className="w-3.5 h-3.5" />
                    {t("advisor.send")}
                  </button>
                </div>
              </div>
            </div>

            <p className="text-center text-xs text-muted-foreground font-body mt-3">
              {t("advisor.disclaimer")}
            </p>
          </TabsContent>

          {/* ── Tab 2: Cases ── */}
          <TabsContent value="vorgaenge" className="mt-0">
            <div className="border border-border rounded-2xl overflow-hidden bg-card shadow-sm">
              <div className="bg-muted border-b border-border px-4 py-3 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400/60" />
                  <div className="w-3 h-3 rounded-full bg-amber-400/60" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400/60" />
                </div>
                <div className="flex-1 mx-3">
                  <div className="bg-background rounded px-3 py-0.5 text-xs text-muted-foreground font-body text-center">
                    rechtimmobilien.de — {t("advisor.tab.cases")}
                  </div>
                </div>
              </div>

              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-display text-lg font-semibold text-foreground">{t("advisor.caseDash")}</h2>
                  <span className="text-xs text-muted-foreground font-body bg-muted px-2.5 py-1 rounded-full">
                    {CASES.length} {t("advisor.cases")}
                  </span>
                </div>

                <div className="space-y-3">
                  {CASES.map((c) => (
                    <CaseCard
                      key={c.id}
                      case={c}
                      statusConfig={statusConfig}
                      stepsLabel={t("case.steps")}
                      deadlineLabel={t("case.deadline")}
                    />
                  ))}
                </div>

                <div className="mt-5 pt-4 border-t border-border">
                  <button
                    onClick={() => setActiveTab("berater")}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-navy text-primary-foreground font-body text-sm font-medium hover:bg-navy-mid transition-colors"
                  >
                    <FileSignature className="w-4 h-4" />
                    {t("advisor.newCase")}
                  </button>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AdvisorPage;
