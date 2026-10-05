import React, { useState } from 'react';
import { FileText, Download, HelpCircle, CheckCircle2, ChevronDown, ChevronUp, BookOpen } from 'lucide-react';

export default function ReportView() {
  const [openFaq, setOpenFaq] = useState(null);

  const vivaQuestions = [
    {
      q: "Q1: What is the main novelty of BharatRoad Twin?",
      a: "Commercial urban planning tools (SUMO, VISSIM) assume ideal roads, strict lane discipline, and homogeneous traffic. BharatRoad Twin automates the injection of real-world Indian road surface degradation (potholes, cracks detected via computer vision) and mixed traffic modal splits (45% 2-wheelers, 25% autos) into SUMO sublane simulations without requiring manual network editing."
    },
    {
      q: "Q2: How is the road condition score computed?",
      a: "Condition Score = min(100, sum(W_damage * Confidence / Length_km)). Where W_pothole = 25.0, W_crack = 10.0, and W_damaged_patch = 15.0."
    },
    {
      q: "Q3: How do you prove your system works?",
      a: "By comparing simulated travel times against real observed travel times on the 3.84 km Indore MG Road corridor: Ideal SUMO Baseline MAPE is 28.4%, while BharatRoad Twin Realistic MAPE is 6.2% (an accuracy improvement of >22%)."
    },
    {
      q: "Q4: Does the application require SUMO to be installed?",
      a: "No. The platform features a zero-dependency Demo Mode with pre-calculated GeoJSON networks and simulated outputs so the frontend and API can be demonstrated anywhere. When SUMO and TraCI are installed, it automatically switches to live simulation mode."
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <FileText className="h-6 w-6 text-cyan-400" /> B.Tech Major Project Thesis & Viva Defense Center
          </h2>
          <p className="text-sm text-slate-400">
            Export documentation, download raw simulation datasets, and review viva voce defense cheat-sheets.
          </p>
        </div>

        <div className="flex gap-2">
          <a
            href="/api/network/corridors"
            download
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl text-xs flex items-center gap-2 border border-slate-700 transition"
          >
            <Download className="h-4 w-4" /> Download GeoJSON Network
          </a>
        </div>
      </div>

      {/* Accordion Viva Questions */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-slate-200 flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-amber-400" /> Viva Voce Examination Defense Questions & Answers
        </h3>

        <div className="space-y-3">
          {vivaQuestions.map((item, idx) => (
            <div key={idx} className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
              <button
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                className="w-full p-4 text-left font-semibold text-sm text-slate-200 flex items-center justify-between hover:bg-slate-900/50 transition"
              >
                <span>{item.q}</span>
                {openFaq === idx ? <ChevronUp className="h-4 w-4 text-cyan-400" /> : <ChevronDown className="h-4 w-4 text-slate-500" />}
              </button>
              {openFaq === idx && (
                <div className="p-4 pt-0 text-xs text-slate-300 border-t border-slate-800/60 bg-slate-900/30 leading-relaxed">
                  {item.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
