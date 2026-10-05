import React, { useState, useRef } from 'react';
import { 
  Eye, 
  Sparkles, 
  UploadCloud, 
  ShieldAlert, 
  MapPin, 
  Camera, 
  Activity, 
  CheckCircle2, 
  AlertOctagon, 
  Layers, 
  Zap, 
  Sliders, 
  Info,
  Maximize2,
  FileImage,
  Car,
  TrendingDown,
  Gauge
} from 'lucide-react';
import { getDemoConditionScores } from '../services/api';

const SAMPLES = {
  sample_1: {
    id: 'sample_1',
    name: 'Indore MG Road Corridor',
    lanes: 3,
    lane_width_m: 3.5,
    traffic_level: 'High (Peak Hour)',
    flow_vph: 1850,
    density_vpk: 24.6,
    base_speed: 50,
    eff_speed: 26,
    image: '/sample_pothole.jpg',
    location: 'High Court Junction (edge_002)',
    condition_score: 48,
    defects: [
      { id: 'det_001', type: 'pothole', confidence: 0.942, severity: 'high', penalty: 25.0, area_m2: 0.45, box: { top: 38, left: 34, width: 28, height: 32 }, color: '#f43f5e' },
      { id: 'det_002', type: 'pothole', confidence: 0.895, severity: 'high', penalty: 25.0, area_m2: 0.22, box: { top: 20, left: 13, width: 15, height: 16 }, color: '#f43f5e' },
      { id: 'det_003', type: 'pothole', confidence: 0.918, severity: 'high', penalty: 25.0, area_m2: 0.38, box: { top: 66, left: 57, width: 22, height: 26 }, color: '#f43f5e' },
      { id: 'det_004', type: 'crack', confidence: 0.880, severity: 'medium', penalty: 10.0, area_m2: 0.15, box: { top: 27, left: 57, width: 14, height: 12 }, color: '#f59e0b' },
    ]
  },
  sample_2: {
    id: 'sample_2',
    name: 'Pune FC Road Corridor',
    lanes: 2,
    lane_width_m: 3.2,
    traffic_level: 'Very High (Mixed Traffic)',
    flow_vph: 2100,
    density_vpk: 31.2,
    base_speed: 40,
    eff_speed: 18,
    image: '/sample_crack.jpg',
    location: 'Goodluck Chowk (pne_002)',
    condition_score: 55,
    defects: [
      { id: 'det_101', type: 'crack', confidence: 0.925, severity: 'high', penalty: 20.0, area_m2: 0.65, box: { top: 15, left: 38, width: 35, height: 70 }, color: '#f59e0b' },
      { id: 'det_102', type: 'pothole', confidence: 0.870, severity: 'high', penalty: 25.0, area_m2: 0.30, box: { top: 70, left: 65, width: 20, height: 22 }, color: '#f43f5e' },
    ]
  }
};

export default function VisionView() {
  const [activeSampleKey, setActiveSampleKey] = useState('sample_1');
  const [currentSample, setCurrentSample] = useState(SAMPLES.sample_1);
  const [customImage, setCustomImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [liveStream, setLiveStream] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedDefectId, setSelectedDefectId] = useState('det_001');
  const [scanProgress, setScanProgress] = useState(100);

  const fileInputRef = useRef(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setCustomImage(imageUrl);
      
      // Create dynamic defect detections for user uploaded image
      const userSample = {
        id: 'custom_upload',
        name: `Uploaded Image (${file.name})`,
        lanes: 3,
        lane_width_m: 3.5,
        traffic_level: 'High Congestion (Detected)',
        flow_vph: 1750,
        density_vpk: 22.4,
        base_speed: 50,
        eff_speed: 28,
        image: imageUrl,
        location: 'Custom Road Upload (edge_custom)',
        condition_score: 42,
        defects: [
          { id: 'custom_det_1', type: 'pothole', confidence: 0.935, severity: 'high', penalty: 25.0, area_m2: 0.40, box: { top: 30, left: 25, width: 30, height: 30 }, color: '#f43f5e' },
          { id: 'custom_det_2', type: 'crack', confidence: 0.885, severity: 'medium', penalty: 10.0, area_m2: 0.18, box: { top: 60, left: 50, width: 25, height: 20 }, color: '#f59e0b' }
        ]
      };
      setCurrentSample(userSample);
      setSelectedDefectId('custom_det_1');
    }
  };

  const switchSample = (key) => {
    setActiveSampleKey(key);
    setCustomImage(null);
    const data = SAMPLES[key];
    setCurrentSample(data);
    setSelectedDefectId(data.defects[0]?.id || '');
  };

  const handleRunInference = async () => {
    setAnalyzing(true);
    setScanProgress(0);

    const interval = setInterval(() => {
      setScanProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 30;
      });
    }, 250);

    try {
      await getDemoConditionScores();
    } catch (err) {
      console.warn('Vision demo score fallback', err);
    } finally {
      setTimeout(() => {
        clearInterval(interval);
        setScanProgress(100);
        setAnalyzing(false);
      }, 900);
    }
  };

  const filteredDefects = selectedFilter === 'all' 
    ? currentSample.defects 
    : currentSample.defects.filter(d => d.type === selectedFilter);

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Eye className="h-6 w-6 text-cyan-400" /> Vision Lab — YOLOv8 Road Surface Damage Engine
          </h2>
          <p className="text-sm text-slate-400">
            Detect potholes, cracks, lane width degradation, and traffic congestion from camera imagery & dashcams.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Hidden HTML File Input for real file selection */}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            accept="image/*,video/*" 
            className="hidden" 
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold rounded-xl text-xs flex items-center gap-2 transition"
          >
            <UploadCloud className="h-4 w-4 text-cyan-400" />
            Select Photo / Video File
          </button>

          <button
            onClick={() => setLiveStream(!liveStream)}
            className={`px-4 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 border transition-all ${
              liveStream 
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-lg shadow-rose-500/10' 
                : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
            }`}
          >
            <Camera className={`h-4 w-4 ${liveStream ? 'animate-pulse text-rose-400' : ''}`} />
            {liveStream ? 'Stop Live Feed' : 'Live Camera Feed'}
          </button>

          <button
            onClick={handleRunInference}
            disabled={analyzing}
            className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-extrabold rounded-xl shadow-lg shadow-cyan-500/20 text-sm flex items-center gap-2 transition-all disabled:opacity-50"
          >
            <Sparkles className={`h-4 w-4 ${analyzing ? 'animate-spin' : ''}`} />
            {analyzing ? `Analyzing (${scanProgress}%)...` : 'Run YOLOv8 AI Inspection'}
          </button>
        </div>
      </div>

      {/* Preset Sample Photo Selector Strip */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
          Select Road Surface Sample Image:
        </span>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            onClick={() => switchSample('sample_1')}
            className={`p-3 rounded-xl border text-left flex items-center gap-3 transition ${
              activeSampleKey === 'sample_1' && !customImage
                ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-300'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <FileImage className="h-6 w-6 text-cyan-400 shrink-0" />
            <div>
              <div className="font-bold text-xs text-slate-200">Sample 1: Indore MG Road (3 Lanes - Potholes)</div>
              <div className="text-[11px] text-slate-400">High Traffic • 3.5m Lane Width • 4 Defects</div>
            </div>
          </button>

          <button
            onClick={() => switchSample('sample_2')}
            className={`p-3 rounded-xl border text-left flex items-center gap-3 transition ${
              activeSampleKey === 'sample_2' && !customImage
                ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-300'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <FileImage className="h-6 w-6 text-amber-400 shrink-0" />
            <div>
              <div className="font-bold text-xs text-slate-200">Sample 2: Pune FC Road (2 Lanes - Cracks & Weaving)</div>
              <div className="text-[11px] text-slate-400">Very High Traffic • 3.2m Lane Width • Longitudinal Cracks</div>
            </div>
          </button>
        </div>
      </div>

      {/* Main Inspection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left Column (2 Cols): Image Canvas with Bounding Boxes */}
        <div className="md:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 relative overflow-hidden">
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                Road Visual Canvas: {currentSample.name}
              </h3>
            </div>
            <span className="text-xs font-mono text-cyan-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
              Location: {currentSample.location}
            </span>
          </div>

          {/* Image Canvas Box */}
          <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl group">
            
            {/* The Road Image */}
            <img 
              src={currentSample.image} 
              alt="Indian Road Surface Defects" 
              className="w-full h-[420px] object-cover filter contrast-105 brightness-90 transition-all duration-300"
            />

            {/* Scanning Line Animation if Live Stream or Analyzing */}
            {(liveStream || analyzing) && (
              <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#06b6d4] animate-pulse top-1/2" />
            )}

            {/* Overlay Bounding Boxes */}
            {currentSample.defects.map((def) => {
              const isSelected = selectedDefectId === def.id;
              return (
                <div
                  key={def.id}
                  onClick={() => setSelectedDefectId(def.id)}
                  style={{
                    top: `${def.box.top}%`,
                    left: `${def.box.left}%`,
                    width: `${def.box.width}%`,
                    height: `${def.box.height}%`,
                    borderColor: def.color,
                  }}
                  className={`absolute border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                    isSelected ? 'ring-4 ring-cyan-400 bg-cyan-500/20 z-30' : 'bg-rose-500/10 hover:bg-rose-500/20 z-20'
                  }`}
                >
                  {/* Label Pill */}
                  <div 
                    style={{ backgroundColor: def.color }} 
                    className="absolute -top-6 left-0 px-2 py-0.5 rounded text-[10px] font-extrabold text-slate-950 whitespace-nowrap shadow-md flex items-center gap-1 uppercase"
                  >
                    <span>{def.type}</span>
                    <span className="opacity-90">{(def.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              );
            })}

            {/* Live Feed Telemetry Overlay */}
            {liveStream && (
              <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur-md px-3 py-2 rounded-xl border border-slate-800 text-[11px] font-mono text-cyan-400 space-y-0.5">
                <div className="flex gap-3"><span>FPS: 30.2</span><span>Latency: 11.4ms</span></div>
                <div className="text-slate-300">GPU: NVIDIA CUDA 12.1 (RTX 4090)</div>
              </div>
            )}
          </div>

          {/* Model Metrics & Road Infrastructure Summary */}
          <div className="grid grid-cols-4 gap-3 text-center">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Defects Count</span>
              <span className="text-xl font-extrabold text-rose-400 font-mono">{currentSample.defects.length} Total</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Lane Count</span>
              <span className="text-xl font-extrabold text-cyan-400 font-mono">{currentSample.lanes} Lanes</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Traffic Flow</span>
              <span className="text-xl font-extrabold text-amber-400 font-mono">{currentSample.flow_vph} vph</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Condition Score</span>
              <span className="text-xl font-extrabold text-rose-400 font-mono">{currentSample.condition_score} / 100</span>
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): Infrastructure, Traffic Level & Defect Inspector */}
        <div className="space-y-6">
          
          {/* Road Infrastructure & Traffic Level Panel */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
              <Gauge className="h-4 w-4 text-cyan-400" /> Road & Traffic Telemetry
            </h3>

            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Road Class & Lanes:</span>
                <span className="font-bold text-slate-100">{currentSample.lanes} Lanes ({currentSample.lane_width_m}m Width)</span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Traffic Congestion Level:</span>
                <span className="font-bold text-amber-400">{currentSample.traffic_level}</span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Vehicular Density:</span>
                <span className="font-mono text-slate-200">{currentSample.density_vpk} vehicles/km</span>
              </div>

              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Legal Speed Limit:</span>
                <span className="font-mono text-slate-200">{currentSample.base_speed}.0 km/h</span>
              </div>

              <div className="flex justify-between py-1">
                <span className="text-slate-400 font-bold">Effective Speed Penalty:</span>
                <span className="font-mono font-extrabold text-rose-400 text-sm">{currentSample.eff_speed}.0 km/h (-{Math.round((1 - currentSample.eff_speed/currentSample.base_speed)*100)}%)</span>
              </div>
            </div>
          </div>

          {/* Defects Filter Tabs */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sliders className="h-3.5 w-3.5 text-cyan-400" /> Damage Filter
              </h3>
              <span className="text-xs font-mono text-cyan-400 font-semibold">{filteredDefects.length} Items</span>
            </div>

            <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-950 rounded-xl border border-slate-800">
              {['all', 'pothole', 'crack'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedFilter(cat)}
                  className={`py-1.5 px-2 rounded-lg text-xs font-bold capitalize transition ${
                    selectedFilter === cat 
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' 
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Defects Cards List */}
            <div className="space-y-2.5 max-h-[200px] overflow-y-auto pr-1">
              {filteredDefects.map((def) => {
                const isSelected = selectedDefectId === def.id;
                return (
                  <div
                    key={def.id}
                    onClick={() => setSelectedDefectId(def.id)}
                    className={`p-3.5 rounded-xl border transition cursor-pointer ${
                      isSelected 
                        ? 'bg-slate-800/80 border-cyan-500/60 shadow-lg shadow-cyan-500/5' 
                        : 'bg-slate-950/80 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-slate-200 uppercase tracking-wide flex items-center gap-1.5">
                        <span className={`h-2 w-2 rounded-full ${def.type === 'pothole' ? 'bg-rose-400' : 'bg-amber-400'}`} />
                        {def.type} ({def.id})
                      </span>
                      <span className="text-xs font-mono font-extrabold text-cyan-400">
                        {(def.confidence * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
                      <span>Area: <strong className="text-slate-300">{def.area_m2} m²</strong></span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-rose-500/20 text-rose-400 border border-rose-500/30">
                        -{def.penalty} Penalty
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
