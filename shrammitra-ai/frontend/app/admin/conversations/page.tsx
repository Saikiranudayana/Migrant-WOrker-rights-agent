"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, Conversation } from "../../../services/api";
import { format } from "date-fns";

const LANGUAGE_FLAGS: Record<string, string> = {
  hi: "🇮🇳 HI",
  kn: "🇮🇳 KN",
  ta: "🇮🇳 TA",
  te: "🇮🇳 TE",
  bn: "🇮🇳 BN",
  en: "🇬🇧 EN",
  or: "🇮🇳 OR",
};

export default function ConversationsPage() {
  const [page, setPage] = useState(0);
  const [language, setLanguage] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["conversations", page, language],
    queryFn: () => api.getConversations({ skip: page * 20, limit: 20, language }),
  });

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Conversations</h1>
        <select
          className="border rounded px-3 py-1.5 text-sm"
          value={language}
          onChange={(e) => { setLanguage(e.target.value); setPage(0); }}
        >
          <option value="">All languages</option>
          {["hi", "kn", "ta", "te", "bn", "en", "or"].map((l) => (
            <option key={l} value={l}>{LANGUAGE_FLAGS[l]}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12">Loading…</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {["ID", "Language", "State", "Messages", "Created"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-gray-600 font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {data?.items?.map((conv: Conversation) => (
                <tr key={conv.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">
                    {conv.id.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3">
                    {LANGUAGE_FLAGS[conv.language] ?? conv.language}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        conv.state === "active"
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {conv.state}
                    </span>
                  </td>
                  <td className="px-4 py-3">{conv.message_count}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {format(new Date(conv.created_at), "dd MMM HH:mm")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex justify-between items-center px-4 py-3 border-t bg-gray-50">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="text-sm px-3 py-1 rounded border disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-sm text-gray-500">Page {page + 1}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!data?.items || data.items.length < 20}
              className="text-sm px-3 py-1 rounded border disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
