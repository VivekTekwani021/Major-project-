import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Activity, 
  Clock, 
  ShieldCheck, 
  Cpu, 
  Sliders, 
  CheckCircle2, 
  AlertTriangle,
  TrendingDown,
  Gauge,
  Flame,
  Users
} from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, AreaChart, Area } from 'recharts';
import { runSimulation } from '../services/api';

export default function SimulationView() {
  const [scenario, setScenario] = useState('realistic'); // 'baseline' or 'realistic'
  const [isRunning, setIsRunning] = useState(false);
  const [simTime, setSimTime] = useState(0);
  const [congestionLevel, setCongestionLevel] = useState('Moderate');
  
  // Traffic fleet distribution sliders
  const [modalSplit, setModalSplit] = useState({
    two_wheeler: 45,
    auto_rickshaw: 25,
    car: 20,
    bus: 5,
    lcv: 5
  });

  const canvasRef = useRef(null);

  // Time-series simulation metrics data
  const [timeSeriesData, setTimeSeriesData] = useState([
    { time: '0m', IdealSpeed: 48, RealisticSpeed: 46, QueueLength: 10, BottleneckDensity: 15 },
    { time: '10m', IdealSpeed: 48, RealisticSpeed: 38, QueueLength: 35, BottleneckDensity: 28 },
    { time: '20m', IdealSpeed: 47, RealisticSpeed: 24, QueueLength: 95, BottleneckDensity: 52 },
    { time: '30m', IdealSpeed: 48, RealisticSpeed: 14, QueueLength: 180, BottleneckDensity: 88 },
    { time: '40m', IdealSpeed: 47, RealisticSpeed: 18, QueueLength: 140, BottleneckDensity: 74 },
    { time: '50m', IdealSpeed: 48, RealisticSpeed: 28, QueueLength: 70, BottleneckDensity: 45 },
    { time: '60m', IdealSpeed: 48, RealisticSpeed: 36, QueueLength: 25, BottleneckDensity: 22 },
  ]);

  // Canvas Traffic Animation Engine
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    // Simulation Vehicles State
    const numVehicles = 24;
    const vehicles = Array.from({ length: numVehicles }, (_, i) => {
      const type = i % 4 === 0 ? 'two_wheeler' : i % 3 === 0 ? 'auto_rickshaw' : i % 5 === 0 ? 'bus' : 'car';
      return {
        id: i,
        x: (i * 45) % canvas.width,
        lane: (i % 3), // 0, 1, 2 sublanes
        speed: type === 'two_wheeler' ? 3.2 : type === 'auto_rickshaw' ? 2.5 : type === 'bus' ? 1.6 : 2.8,
        type: type,
        color: type === 'two_wheeler' ? '#f43f5e' : type === 'auto_rickshaw' ? '#f59e0b' : type === 'bus' ? '#10b981' : '#3b82f6',
        width: type === 'two_wheeler' ? 12 : type === 'auto_rickshaw' ? 18 : type === 'bus' ? 38 : 24,
        height: type === 'two_wheeler' ? 6 : type === 'auto_rickshaw' ? 10 : type === 'bus' ? 14 : 11,
      };
    });

    const potholeZoneX = canvas.width * 0.55;

    const render = () => {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Road Lanes
      const laneHeight = canvas.height / 3;
      ctx.strokeStyle = '#334155';
      ctx.setLineDash([12, 12]);
      ctx.lineWidth = 1.5;
      
      for (let i = 1; i < 3; i++) {
        ctx.beginPath();
        ctx.moveTo(0, i * laneHeight);
        ctx.lineTo(canvas.width, i * laneHeight);
        ctx.stroke();
      }
      ctx.setLineDash([]); // Reset line dash

      // Draw Pothole Damage Bottleneck Zone in Realistic Mode
      if (scenario === 'realistic') {
        ctx.fillStyle = 'rgba(244, 63, 94, 0.25)';
        ctx.fillRect(potholeZoneX - 25, 10, 55, canvas.height - 20);

        // Pothole circles
        ctx.fillStyle = '#f43f5e';
        ctx.beginPath();
        ctx.arc(potholeZoneX, laneHeight * 1.5, 16, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.arc(potholeZoneX + 15, laneHeight * 0.5, 10, 0, Math.PI * 2);
        ctx.fill();

        // Label
        ctx.fillStyle = '#f43f5e';
        ctx.font = 'bold 10px sans-serif';
        ctx.fillText('POTHOLE BOTTLENECK (SPEED DROP)', potholeZoneX - 55, 14);
      }

      // Update & Draw Vehicles
      vehicles.forEach(v => {
        if (isRunning) {
          let currentSpeed = v.speed;

          // In realistic mode, vehicles slow down at pothole bottleneck and 2-wheelers filter laterally
          if (scenario === 'realistic' && Math.abs(v.x - potholeZoneX) < 80) {
            if (v.type === 'two_wheeler') {
              currentSpeed = v.speed * 0.75; // 2-wheelers squeeze & filter around pothole
            } else {
              currentSpeed = v.speed * 0.25; // Cars & buses queue up
            }
          }

          v.x += currentSpeed;
          if (v.x > canvas.width + 40) {
            v.x = -30;
          }
        }

        // Draw vehicle body
        const y = v.lane * laneHeight + (laneHeight - v.height) / 2;
        ctx.fillStyle = v.color;
        ctx.beginPath();
        ctx.roundRect(v.x, y, v.width, v.height, 3);
        ctx.fill();

        // Highlight 2-wheeler sublane lateral filtering
        if (scenario === 'realistic' && v.type === 'two_wheeler' && Math.abs(v.x - potholeZoneX) < 90) {
          ctx.strokeStyle = '#f43f5e';
          ctx.lineWidth = 1;
          ctx.strokeRect(v.x - 2, y - 2, v.width + 4, v.height + 4);
        }
      });

      if (isRunning) {
        setSimTime(prev => prev + 0.1);
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [scenario, isRunning]);

  const toggleSimulation = () => {
    setIsRunning(!isRunning);
  };

  const resetSimulation = () => {
    setIsRunning(false);
    setSimTime(0);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Activity className="h-6 w-6 text-cyan-400" /> Indian Traffic Congestion & Sublane Flow Simulator
          </h2>
          <p className="text-sm text-slate-400">
            Simulate dynamic traffic queue formation, shockwave bottlenecks, and sublane filtering caused by road defects.
          </p>
        </div>

        {/* Play / Pause / Reset Simulation Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={resetSimulation}
            className="px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-bold rounded-xl text-xs flex items-center gap-2 transition"
          >
            <RotateCcw className="h-4 w-4" /> Reset
          </button>

          <button
            onClick={toggleSimulation}
            className={`px-6 py-2.5 font-extrabold rounded-xl shadow-lg text-sm flex items-center gap-2 transition-all ${
              isRunning 
                ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20' 
                : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 shadow-cyan-500/20'
            }`}
          >
            {isRunning ? <Pause className="h-4 w-4 fill-slate-950" /> : <Play className="h-4 w-4 fill-slate-950" />}
            {isRunning ? 'Pause Traffic Sim' : 'Start Live Traffic Simulation'}
          </button>
        </div>
      </div>

      {/* Scenario Toggle Banner */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Simulation Mode:</span>
          <div className="grid grid-cols-2 gap-1 p-1 bg-slate-950 rounded-xl border border-slate-800">
            <button
              onClick={() => setScenario('baseline')}
              className={`py-1.5 px-3 rounded-lg text-xs font-bold transition ${
                scenario === 'baseline' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Ideal Homogeneous Road
            </button>
            <button
              onClick={() => setScenario('realistic')}
              className={`py-1.5 px-3 rounded-lg text-xs font-bold transition ${
                scenario === 'realistic' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Indian Mixed Traffic + Potholes
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
            <span className="text-slate-300">2-Wheelers (45%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
            <span className="text-slate-300">Autos (25%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />
            <span className="text-slate-300">Cars (20%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-300">Buses (10%)</span>
          </div>
        </div>
      </div>

      {/* Live 2D Sublane Traffic Motion Canvas */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Flame className="h-4 w-4 text-cyan-400" /> 2D Sublane Vehicle Motion & Bottleneck Queue Visualizer
          </h3>
          <span className="text-xs font-mono text-cyan-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
            Sim Time: {simTime.toFixed(1)}s | {scenario === 'realistic' ? 'Pothole Bottleneck Active' : 'Ideal Uniform Speed'}
          </span>
        </div>

        {/* The 2D Canvas */}
        <canvas 
          ref={canvasRef} 
          width={800} 
          height={160} 
          className="w-full h-44 rounded-xl border border-slate-800 bg-slate-950 shadow-2xl"
        />

        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>← Corridor Entry (Free Flow $50\text{ km/h}$)</span>
          <span className={scenario === 'realistic' ? 'text-rose-400 font-bold' : 'text-slate-400'}>
            {scenario === 'realistic' ? '⚠️ Pothole Queue Spillback Zone' : 'Ideal Lane Discipline'}
          </span>
          <span>Corridor Exit →</span>
        </div>
      </div>

      {/* Real-time Congestion Analytics Graphs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Speed Profile Drop Graph */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-rose-400" /> Average Speed Drop Over Corridor ($km/h$)
          </h3>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} domain={[0, 60]} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '5px' }} />
                <Line type="monotone" dataKey="IdealSpeed" name="Ideal Road Speed (km/h)" stroke="#3b82f6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="RealisticSpeed" name="Indian Pothole Twin Speed (km/h)" stroke="#f43f5e" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Traffic Queue Spillback Graph */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Users className="h-4 w-4 text-amber-400" /> Traffic Queue Length & Bottleneck Density
          </h3>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#f8fafc' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '5px' }} />
                <Area type="monotone" dataKey="QueueLength" name="Queue Spillback (meters)" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
