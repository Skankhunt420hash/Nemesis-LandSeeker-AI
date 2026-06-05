import React, { useEffect, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import LegalDisclaimer from "./pages/LegalDisclaimer";

const nativeShell = Boolean(window.Capacitor?.isNativePlatform?.());
const defaultApiBase = nativeShell ? (localStorage.getItem("landseeker_api_base") || "") : window.location.origin;

function friendlyStatus(state) {
  if (state === "SUCCESS") return "Fertig";
  if (state === "FAILURE") return "Fehlgeschlagen";
  if (state === "PENDING") return "Wartet";
  if (state === "STARTED") return "Laeuft";
  return state || "Bereit";
}

function SignalPill({ children, tone = "slate" }) {
  const tones = {
    emerald: "bg-emerald-100 text-emerald-800 border-emerald-200",
    amber: "bg-amber-100 text-amber-800 border-amber-200",
    slate: "bg-slate-100 text-slate-700 border-slate-200",
  };
  return <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${tones[tone]}`}>{children}</span>;
}

function SectionCard({ title, subtitle, children }) {
  return (
    <section className="rounded-[30px] border border-white/70 bg-white/85 p-5 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
      <div className="mb-4">
        <h2 className="text-lg font-black tracking-tight text-slate-900">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-slate-600">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}

function HintBox() {
  return (
    <div className="rounded-[28px] border border-amber-200 bg-amber-50/90 p-5 text-sm shadow-sm">
      <h2 className="mb-2 text-base font-semibold">Rechtlicher Hinweis</h2>
      <p>Art. 658 ZGB: Eine Aneignung ist nur moeglich, wenn das Grundbuch ein Grundstueck ausdruecklich als herrenlos ausweist.</p>
      <p className="mt-2 font-semibold">Jeder Treffer muss beim zustaendigen Grundbuchamt verifiziert werden.</p>
    </div>
  );
}

function NativeSetup({ apiBase, setApiBase, onSave, health }) {
  if (!nativeShell) {
    return null;
  }

  return (
    <SectionCard
      title="Native App Verbindung"
      subtitle="Die Android-App laeuft nativ. Fuer Recherche und Celery braucht sie eine erreichbare FastAPI-Instanz, z. B. deinen Rechner im selben WLAN."
    >
      <div className="space-y-3">
        <input
          className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm"
          placeholder="http://192.168.1.20:8000"
          value={apiBase}
          onChange={(event) => setApiBase(event.target.value)}
        />
        <div className="flex flex-wrap gap-2">
          <button className="rounded-full bg-emerald-700 px-4 py-2 text-sm font-semibold text-white" onClick={onSave}>
            Server speichern
          </button>
          <SignalPill tone={health?.ok ? "emerald" : "amber"}>{health?.ok ? "Verbunden" : "Nicht verbunden"}</SignalPill>
        </div>
      </div>
    </SectionCard>
  );
}

export default function App() {
  if (window.location.pathname === "/legal") {
    return <LegalDisclaimer />;
  }

  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [cantons, setCantons] = useState([]);
  const [rows, setRows] = useState([]);
  const [filterCanton, setFilterCanton] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [selected, setSelected] = useState(null);
  const [letter, setLetter] = useState("");
  const [health, setHealth] = useState(null);
  const [statusMessage, setStatusMessage] = useState("");

  const [uploadFile, setUploadFile] = useState(null);
  const [jobId, setJobId] = useState("");
  const [jobStatus, setJobStatus] = useState("");

  const [wfsUrl, setWfsUrl] = useState("");
  const [wfsType, setWfsType] = useState("");
  const [wfsMeta, setWfsMeta] = useState(null);

  const base = apiBase || window.location.origin;
  const mapRows = rows.filter((row) => row.latitude && row.longitude);

  const fetchJson = async (path, options = {}) => {
    const response = await fetch(`${base}${path}`, options);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  };

  const saveApiBase = () => {
    localStorage.setItem("landseeker_api_base", apiBase.trim());
    setStatusMessage("Server-Adresse gespeichert.");
  };

  const load = async () => {
    try {
      const [cantonData, rowData, healthData] = await Promise.all([
        fetchJson("/cantons"),
        fetchJson(`/candidates?${new URLSearchParams({
          ...(filterCanton ? { canton: filterCanton } : {}),
          min_score: String(minScore),
        })}`),
        fetchJson("/health"),
      ]);
      setCantons(cantonData);
      setRows(rowData);
      setHealth(healthData);
      setStatusMessage("");
    } catch (error) {
      setHealth({ ok: false, celery_enabled: false });
      setStatusMessage("Verbindung fehlgeschlagen. Bitte Server-Adresse und gestartetes Backend pruefen.");
    }
  };

  useEffect(() => {
    if (base) {
      load();
    }
  }, [filterCanton, minScore, base]);

  const updateStatus = async (id, verification_status) => {
    await fetchJson(`/candidates/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ verification_status }),
    });
    load();
  };

  const makeLetter = async (id, lang = "de") => {
    const response = await fetchJson(`/candidates/${id}/letter?lang=${lang}`);
    setLetter(response.text);
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      return;
    }
    const formData = new FormData();
    formData.append("file", uploadFile);
    const response = await fetch(`${base}/ingest/upload`, { method: "POST", body: formData }).then((r) => r.json());
    if (response.task_id) {
      setJobId(response.task_id);
      setJobStatus("Warteschlange");
    } else {
      setJobStatus(`Direkt importiert: ${response.created || 0}`);
      load();
    }
  };

  const checkTask = async () => {
    if (!jobId) {
      return;
    }
    const response = await fetchJson(`/tasks/${jobId}`);
    setJobStatus(`${friendlyStatus(response.state)}${response.result ? ` - ${JSON.stringify(response.result)}` : ""}`);
    if (response.state === "SUCCESS") {
      load();
    }
  };

  const loadWfsMeta = async () => {
    const response = await fetchJson("/ingest/wfs/metadata", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: wfsUrl }),
    });
    setWfsMeta(response);
  };

  const importWfs = async () => {
    const response = await fetchJson("/ingest/wfs/features", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: wfsUrl, type_name: wfsType, limit: 200 }),
    });
    if (response.task_id) {
      setJobId(response.task_id);
      setJobStatus("Warteschlange");
    } else {
      setJobStatus(`Direkt importiert: ${response.created || 0}`);
      load();
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,#fff7ed,transparent_32%),radial-gradient(circle_at_right,#dcfce7,transparent_28%),linear-gradient(180deg,#fffdf8_0%,#f8fafc_38%,#ecfeff_100%)] text-slate-900">
      <header className="sticky top-0 z-20 border-b border-white/60 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-4 sm:px-6">
          <div className="flex-1">
            <div className="text-[11px] uppercase tracking-[0.34em] text-emerald-700">LandSeeker AI</div>
            <h1 className="text-3xl font-black tracking-tight">Frohe Schweizer Land-Recherche</h1>
            <p className="mt-1 max-w-2xl text-sm text-slate-600">
              Native Android-App und Desktop-Oberflaeche fuer Kandidatenrecherche, Kartenansicht und Grundbuchamt-Anfragen.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <SignalPill tone={health?.ok ? "emerald" : "amber"}>{health?.ok ? "Online" : "Offline"}</SignalPill>
            <SignalPill tone="slate">{health?.celery_enabled ? "Celery aktiv" : "Celery aus"}</SignalPill>
            <a className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" href="/legal">
              Disclaimer
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 xl:grid-cols-[1.7fr_0.95fr]">
        <section className="space-y-6">
          <NativeSetup apiBase={apiBase} setApiBase={setApiBase} onSave={saveApiBase} health={health} />

          {statusMessage ? (
            <div className="rounded-[26px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">{statusMessage}</div>
          ) : null}

          <SectionCard title="Karte und Filter" subtitle="Schneller Ueberblick ueber moegliche Kandidaten, optimiert fuer Desktop und Smartphone.">
            <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
              <select className="rounded-full border border-slate-300 px-4 py-3 text-sm" value={filterCanton} onChange={(event) => setFilterCanton(event.target.value)}>
                <option value="">Alle Kantone</option>
                {cantons.map((canton) => (
                  <option key={canton.code} value={canton.code}>
                    {canton.code} - {canton.name}
                  </option>
                ))}
              </select>
              <label className="flex items-center justify-between gap-3 rounded-full border border-slate-300 px-4 py-3 text-sm">
                <span>Min-Score</span>
                <input className="w-28" type="range" min="0" max="100" value={minScore} onChange={(event) => setMinScore(event.target.value)} />
                <span className="min-w-8 text-right font-semibold">{minScore}</span>
              </label>
              <div className="flex flex-wrap gap-2 sm:ml-auto">
                <a className="rounded-full border border-emerald-300 px-4 py-2 text-sm font-semibold text-emerald-800" href={`${base}/export/csv`}>
                  CSV Export
                </a>
                <a className="rounded-full border border-emerald-300 px-4 py-2 text-sm font-semibold text-emerald-800" href={`${base}/export/pdf`}>
                  PDF Export
                </a>
              </div>
            </div>

            <div className="overflow-hidden rounded-[24px]">
              <MapContainer center={[46.8, 8.2]} zoom={8} className="h-[18rem] sm:h-[24rem]">
                <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                {mapRows.map((row) => (
                  <Marker key={row.id} position={[row.latitude, row.longitude]}>
                    <Popup>
                      {row.municipality} #{row.parcel_number}
                      <br />
                      Score {row.confidence_score}
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </SectionCard>

          <SectionCard title="Import und Scanner" subtitle="Datei-Import, WFS-Metadaten und Celery-Status in einer einfachen Arbeitsflaeche.">
            <div className="space-y-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
                <input className="max-w-full text-sm" type="file" onChange={(event) => setUploadFile(event.target.files?.[0] || null)} />
                <button className="rounded-full bg-emerald-700 px-4 py-3 text-sm font-semibold text-white" onClick={handleUpload}>
                  Datei importieren
                </button>
              </div>

              <div className="grid gap-3 md:grid-cols-[1.2fr_1fr_auto]">
                <input className="rounded-2xl border border-slate-300 px-4 py-3 text-sm" placeholder="WFS URL" value={wfsUrl} onChange={(event) => setWfsUrl(event.target.value)} />
                <input className="rounded-2xl border border-slate-300 px-4 py-3 text-sm" placeholder="TypeName / Layer" value={wfsType} onChange={(event) => setWfsType(event.target.value)} />
                <div className="flex flex-col gap-2 sm:flex-row">
                  <button className="rounded-full border border-slate-300 px-4 py-3 text-sm font-semibold" onClick={loadWfsMeta}>
                    Metadaten
                  </button>
                  <button className="rounded-full bg-emerald-700 px-4 py-3 text-sm font-semibold text-white" onClick={importWfs}>
                    WFS importieren
                  </button>
                </div>
              </div>

              {wfsMeta?.feature_types ? (
                <div className="max-h-36 overflow-auto rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs">
                  {wfsMeta.feature_types.slice(0, 20).map((feature) => (
                    <div key={feature.name}>
                      {feature.name} - {feature.title}
                    </div>
                  ))}
                </div>
              ) : null}

              <div className="flex flex-col gap-3 rounded-2xl bg-slate-100 px-4 py-4 text-sm sm:flex-row sm:flex-wrap sm:items-center">
                <span className="font-semibold">Celery Job:</span>
                <span>{jobId || "-"}</span>
                <span className="text-slate-600">{jobStatus || "Noch kein Job gestartet"}</span>
                <button className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold" onClick={checkTask}>
                  Status pruefen
                </button>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Kandidatenliste" subtitle="Grosse Treffer zuerst. Tippe einen Eintrag an, um Details und den Briefgenerator zu sehen.">
            <div className="space-y-3">
              {rows.map((row) => (
                <button
                  key={row.id}
                  className={`w-full rounded-[22px] border px-4 py-4 text-left transition ${selected?.id === row.id ? "border-emerald-400 bg-emerald-50" : "border-slate-200 bg-white hover:border-emerald-200 hover:bg-emerald-50/50"}`}
                  onClick={() => setSelected(row)}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="text-base font-bold">{row.municipality} #{row.parcel_number}</div>
                      <div className="mt-1 text-sm text-slate-600">{row.canton} · {row.land_type || "Unbekannt"}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <SignalPill tone="emerald">Score {row.confidence_score}</SignalPill>
                      <SignalPill tone="amber">Risiko {row.risk_score}</SignalPill>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </SectionCard>
        </section>

        <aside className="space-y-6">
          <HintBox />

          <SectionCard title="Research Assistant" subtitle="Kurze Bewertung, Risiken und naechster Schritt.">
            <p className="text-sm text-slate-600">This is not legal advice. Verify with the responsible Grundbuchamt.</p>
            {selected ? (
              <div className="mt-4 space-y-3 text-sm">
                <div><b>Parzelle:</b> {selected.parcel_number} ({selected.municipality})</div>
                <div><b>Warum markiert:</b> {(selected.candidate_signals || []).join(", ") || "Kein direkter Herrenlos-Hinweis"}</div>
                <div><b>Regel:</b> Art. 658 ZGB verlangt Registerbestaetigung.</div>
                <div><b>Risiko:</b> {selected.risk_score} / 100</div>
                <div><b>Naechster Schritt:</b> Brief ans Grundbuchamt erzeugen und Eintrag pruefen lassen.</div>
                <div className="flex flex-wrap gap-2 pt-2">
                  <button className="rounded-full bg-emerald-700 px-4 py-2 text-sm font-semibold text-white" onClick={() => makeLetter(selected.id, "de")}>
                    Brief DE
                  </button>
                  <button className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold" onClick={() => makeLetter(selected.id, "fr")}>
                    FR
                  </button>
                  <button className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold" onClick={() => makeLetter(selected.id, "it")}>
                    IT
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold" onClick={() => updateStatus(selected.id, "verified")}>
                    Verifiziert
                  </button>
                  <button className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold" onClick={() => updateStatus(selected.id, "rejected")}>
                    Abgelehnt
                  </button>
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm text-slate-600">Waehle einen Kandidaten aus. Auf dem Smartphone liegt dieser Bereich direkt unter der Liste.</p>
            )}
          </SectionCard>

          {letter ? (
            <SectionCard title="Briefentwurf" subtitle="Vorfertige Anfrage an das Grundbuchamt.">
              <textarea className="h-80 w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs" value={letter} readOnly />
            </SectionCard>
          ) : null}
        </aside>
      </main>
    </div>
  );
}
