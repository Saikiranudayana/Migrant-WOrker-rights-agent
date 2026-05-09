"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, Source } from "@/services/api";
import { format } from "date-fns";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  pending: "bg-yellow-100 text-yellow-700",
  error: "bg-red-100 text-red-700",
  inactive: "bg-gray-100 text-gray-500",
};

export default function SourcesPage() {
  const qc = useQueryClient();
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ["sources", page],
    queryFn: () => api.getSources({ skip: page * 20, limit: 20 }),
  });

  const reindexMutation = useMutation({
    mutationFn: api.triggerReindex,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sources"] });
      alert("Reindex triggered!");
    },
  });

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Document Sources</h1>
        <button
          onClick={() => reindexMutation.mutate()}
          disabled={reindexMutation.isPending}
          className="px-4 py-2 bg-brand text-white rounded-lg text-sm hover:bg-brand-dark disabled:opacity-50"
        >
          {reindexMutation.isPending ? "Triggering…" : "Re-index All"}
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">Loading…</div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {["Title", "Type", "Chunks", "Status", "Last Synced"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-gray-600 font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {data?.items?.map((src: Source) => (
                <tr key={src.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <a
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brand hover:underline"
                    >
                      {src.title}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{src.source_type}</td>
                  <td className="px-4 py-3">{src.chunk_count ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        STATUS_COLORS[src.status] ?? ""
                      }`}
                    >
                      {src.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {src.last_synced_at
                      ? format(new Date(src.last_synced_at), "dd MMM HH:mm")
                      : "Never"}
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
