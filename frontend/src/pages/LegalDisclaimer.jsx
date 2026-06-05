import React from "react";

export default function LegalDisclaimer() {
  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#fffaf2_0%,#f8fafc_40%,#ecfeff_100%)] px-4 py-8 text-slate-900 sm:px-6">
      <div className="mx-auto max-w-3xl rounded-[32px] border border-white/70 bg-white/85 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
        <div className="text-[11px] uppercase tracking-[0.34em] text-emerald-700">LandSeeker AI</div>
        <h1 className="mt-2 text-3xl font-black tracking-tight">Rechtlicher Disclaimer</h1>
        <div className="mt-5 space-y-4 text-sm leading-6 text-slate-700">
          <p>LandSeeker AI ist ausschliesslich ein Recherche-Werkzeug. Die App markiert moegliche Kandidaten auf Basis oeffentlicher Daten und nutzerseitig geladener Dateien.</p>
          <p>Massgebliche Rechtsgrundlage ist Art. 658 ZGB. Ein eingetragenes Grundstueck kann nur angeeignet werden, wenn das Grundbuch es ausdruecklich als herrenlos ausweist.</p>
          <p className="font-semibold text-slate-900">Jeder Kandidat muss vor jedem rechtlichen Schritt beim zustaendigen Grundbuchamt verifiziert werden.</p>
          <p>Die App bietet keine Rechtsberatung. Es werden keine automatischen Anspruchserklaerungen, Einreichungen oder Verfuegungen erzeugt.</p>
        </div>
        <a className="mt-6 inline-flex rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700" href="/">
          Zurueck zur App
        </a>
      </div>
    </div>
  );
}
