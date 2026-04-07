import React from 'react';
import { 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, BarChart, Bar 
} from 'recharts';
import { motion } from 'framer-motion';
import { TrendingUp, Activity, BarChart3, CheckCircle2, X } from 'lucide-react';
import type { MetricsData, ImprovementsData } from '../types';

interface MetricsDashboardProps {
  metrics: MetricsData | null;
  improvements: ImprovementsData | null;
  onClose: () => void;
}

const MetricsDashboard: React.FC<MetricsDashboardProps> = ({ metrics, improvements, onClose }) => {
  if (!metrics) return null;

  // Prepare data for charts
  const historyData = metrics.daily_history.map(d => ({
    name: new Date(d.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    faithfulness: d.avg_faithfulness * 100,
    relevance: d.avg_relevance * 100,
    accuracy: (d as any).avg_accuracy * 100 || 0,
    questions: d.total_questions,
    rating: d.avg_rating * 20 // scale out of 100 for comparison
  }));

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="fixed inset-0 z-50 p-6 flex flex-col bg-[#05070a]/90 backdrop-blur-2xl overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
            System Intelligence Dashboard
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Real-time performance metrics and automated self-improvement insights.
          </p>
        </div>
        <button 
          onClick={onClose}
          className="p-2 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-all ring-1 ring-white/10"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-8 custom-scrollbar">
        {/* Top Cards: Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: 'Avg Faithfulness', value: `${Math.round(metrics.avg_faithfulness * 100)}%`, color: 'text-emerald-400', icon: CheckCircle2 },
            { label: 'Avg Relevance', value: `${Math.round(metrics.avg_relevance * 100)}%`, color: 'text-indigo-400', icon: Activity },
            { label: 'Avg Accuracy', value: `${Math.round((metrics as any).avg_accuracy * 100)}%`, color: 'text-cyan-400', icon: TrendingUp },
            { label: 'Total Queries', value: metrics.total_questions, color: 'text-slate-200', icon: BarChart3 },
          ].map((stat, i) => (
            <div key={i} className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
              <div className="flex items-center gap-3 text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
                <stat.icon className="w-4 h-4" />
                {stat.label}
              </div>
              <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Quality Trends */}
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 h-[350px] flex flex-col">
            <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-6 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-400" />
              Quality Trends (Last 7 Days)
            </h3>
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historyData}>
                  <defs>
                    <linearGradient id="colorF" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorR" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorA" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #ffffff10', borderRadius: '12px' }}
                    itemStyle={{ fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="faithfulness" stroke="#10b981" fillOpacity={1} fill="url(#colorF)" strokeWidth={2} name="Faithfulness" />
                  <Area type="monotone" dataKey="relevance" stroke="#6366f1" fillOpacity={1} fill="url(#colorR)" strokeWidth={2} name="Relevance" />
                  <Area type="monotone" dataKey="accuracy" stroke="#22d3ee" fillOpacity={1} fill="url(#colorA)" strokeWidth={2} name="Accuracy" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Activity Bar Chart */}
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 h-[350px] flex flex-col">
            <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-400 mb-6 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              Daily Question Volume
            </h3>
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={historyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip 
                    cursor={{fill: '#ffffff05'}}
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #ffffff10', borderRadius: '12px' }}
                  />
                  <Bar dataKey="questions" fill="#0ea5e9" radius={[4, 4, 0, 0]} name="Queries" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Insights Section */}
        <div className="p-8 rounded-3xl bg-indigo-500/5 border border-indigo-500/20 ring-1 ring-indigo-500/10">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center">
              <TrendingUp className="text-indigo-400 w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">Self-Improvement Engine</h3>
              <p className="text-sm text-slate-400">Automated pattern recognition based on user feedback.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {improvements?.insights.map((insight, idx) => (
              <div key={idx} className="p-5 rounded-2xl bg-[#0f172a] border border-white/5 hover:border-indigo-500/50 transition-all group">
                <div className="flex items-center justify-between mb-4">
                  <span className="px-2 py-1 bg-white/5 rounded text-[10px] font-bold text-slate-500 uppercase tracking-tighter">
                    {insight.metric}
                  </span>
                  <div className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                    insight.trend === 'improving' ? 'bg-emerald-500/10 text-emerald-400' :
                    insight.trend === 'declining' ? 'bg-rose-500/10 text-rose-400' :
                    'bg-sky-500/10 text-sky-400'
                  }`}>
                    {insight.trend}
                  </div>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed mb-4 italic">
                  "{insight.suggestion}"
                </p>
                <div className="flex items-center justify-between mt-auto pt-4 border-t border-white/5">
                  <div className="text-[10px] text-slate-500 font-mono">
                    CONFIDENCE: {Math.round(insight.confidence_score * 100)}%
                  </div>
                  {insight.auto_applied && (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" />
                      RESOLVED
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default MetricsDashboard;
