"use client";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { api } from "../../../services/api";

const LANGUAGE_COLORS: Record<string, string> = {
  hi: "#3b82f6",
  kn: "#f59e0b",
  ta: "#10b981",
  te: "#ef4444",
  bn: "#8b5cf6",
  en: "#6b7280",
  or: "#f97316",
};

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-xl shadow p-5">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  );
}

export default function AnalyticsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics"],
    queryFn: api.getAnalytics,
  });

  if (isLoading) return <div className="p-8 text-center">Loading…</div>;
  if (error || !data)
    return <div className="p-8 text-center text-red-500">Failed to load analytics.</div>;

  const languagePieData = Object.entries(data.language_breakdown).map(
    ([lang, count]) => ({ name: lang.toUpperCase(), value: count as number })
  );

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Analytics</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Conversations" value={data.total_conversations} />
        <StatCard label="Active Now" value={data.active_conversations} />
        <StatCard label="Total Messages" value={data.total_messages} />
        <StatCard label="Voice Sessions" value={data.voice_count} />
        <StatCard
          label="Avg Confidence"
          value={`${(data.avg_confidence * 100).toFixed(1)}%`}
        />
        <StatCard label="Avg Latency" value={`${data.avg_latency_ms.toFixed(0)}ms`} />
        <StatCard
          label="Avg Rating"
          value={data.avg_rating ? data.avg_rating.toFixed(1) + " / 5" : "—"}
        />
      </div>

      {/* Language breakdown */}
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Language Breakdown</h2>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={languagePieData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={({ name, percent }) =>
                `${name} ${(percent * 100).toFixed(0)}%`
              }
            >
              {languagePieData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={LANGUAGE_COLORS[entry.name.toLowerCase()] ?? "#9ca3af"}
                />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
