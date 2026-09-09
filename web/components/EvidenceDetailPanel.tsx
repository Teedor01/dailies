"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import type { EvidenceEntry } from "@/lib/types";
import { EvidenceTypeBadge } from "./EvidenceTypeBadge";


function extractTable(resultSample: unknown): { columns: string[]; rows: unknown[][] } | null {
  if (!resultSample || typeof resultSample !== "object") return null;
  const rs = resultSample as Record<string, unknown>;
  const content = rs.content as Array<{ type?: string; text?: string }> | undefined;
  const text = content?.[0]?.text;
  if (typeof text === "string") {
    try {
      const parsed = JSON.parse(text);
      if (Array.isArray(parsed.columns) && Array.isArray(parsed.rows)) {
        return { columns: parsed.columns, rows: parsed.rows };
      }
    } catch {
    }
  }
  return null;
}

function isErrorResult(resultSample: unknown): boolean {
  if (!resultSample || typeof resultSample !== "object") return false;
  return Boolean((resultSample as Record<string, unknown>).isError);
}

function rawErrorText(resultSample: unknown): string | null {
  if (!resultSample || typeof resultSample !== "object") return null;
  const rs = resultSample as Record<string, unknown>;
  const content = rs.content as Array<{ text?: string }> | undefined;
  return content?.[0]?.text ?? null;
}

function inferSource(entry: EvidenceEntry): string {
  if (entry.sql) return "agent_query";
  if (entry.step === "OBSERVE") return "deterministic_scan";
  return "agent_reasoning";
}

export function EvidenceDetailPanel({ entry }: { entry: EvidenceEntry }) {
  const [copied, setCopied] = useState(false);
  const table = extractTable(entry.result_sample);
  const errored = isErrorResult(entry.result_sample);
  const errorText = errored ? rawErrorText(entry.result_sample) : null;

  const handleCopy = () => {
    if (!entry.sql) return;
    navigator.clipboard.writeText(entry.sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-2 space-y-4">
        <div className="rounded-xl border border-zinc-200 bg-white p-4">
          <div className="mb-2 flex items-center gap-2">
            <span className="font-mono text-sm font-semibold text-zinc-900">{entry.id}</span>
            <EvidenceTypeBadge type={entry.entry_type} />
            {errored && (
              <span className="inline-flex items-center rounded-md bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700">
                query failed
              </span>
            )}
          </div>
          <p className="text-sm text-zinc-500 mb-1">
            Step: <span className="font-medium text-zinc-700">{entry.step}</span>
          </p>
          <p className="text-sm text-zinc-800">{entry.claim}</p>
        </div>

        {errored && errorText && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4">
            <div className="mb-1 text-xs font-semibold uppercase text-red-700">
              ClickHouse Error
            </div>
            <p className="font-mono text-xs text-red-800 break-words">{errorText}</p>
          </div>
        )}

        {table && (
          <div className="rounded-xl border border-zinc-200 bg-white p-4">
            <div className="mb-2 text-sm font-semibold text-zinc-900">
              Result Sample (first {Math.min(5, table.rows.length)} rows)
            </div>
            <div className="thin-scroll overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-zinc-200 text-zinc-500">
                    {table.columns.map((c) => (
                      <th key={c} className="whitespace-nowrap py-1.5 pr-4 font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {table.rows.slice(0, 5).map((row, i) => (
                    <tr key={i} className="border-b border-zinc-100 last:border-0">
                      {row.map((cell, j) => (
                        <td key={j} className="whitespace-nowrap py-1.5 pr-4 text-zinc-700">
                          {String(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-2 text-xs text-zinc-400">Total rows: {table.rows.length}</div>
          </div>
        )}

        {entry.sql && (
          <div className="rounded-xl border border-zinc-200 bg-white p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-semibold text-zinc-900">SQL Query</span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 rounded-md border border-zinc-200 px-2 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <pre className="thin-scroll overflow-x-auto rounded-lg bg-zinc-900 p-3 text-xs text-zinc-100">
              <code>{entry.sql}</code>
            </pre>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <div className="mb-3 text-sm font-semibold text-zinc-900">Details</div>
        <dl className="space-y-2.5 text-xs">
          <div className="flex items-center justify-between">
            <dt className="text-zinc-500">Type</dt>
            <dd><EvidenceTypeBadge type={entry.entry_type} /></dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-zinc-500">Step</dt>
            <dd className="font-medium text-zinc-700">{entry.step}</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-zinc-500">Timestamp</dt>
            <dd className="font-medium text-zinc-700">
              {new Date(entry.timestamp).toLocaleString()}
            </dd>
          </div>
          {table && (
            <div className="flex items-center justify-between">
              <dt className="text-zinc-500">Row Count</dt>
              <dd className="font-medium text-zinc-700">{table.rows.length}</dd>
            </div>
          )}
          <div className="flex items-center justify-between">
            <dt className="text-zinc-500">Source</dt>
            <dd className="font-mono text-zinc-700">{inferSource(entry)}</dd>
          </div>
          {entry.supports.length > 0 && (
            <div>
              <dt className="mb-1 text-zinc-500">Supports</dt>
              <dd className="flex flex-wrap gap-1">
                {entry.supports.map((id) => (
                  <span
                    key={id}
                    className="rounded-md bg-zinc-100 px-1.5 py-0.5 font-mono text-[11px] text-zinc-700"
                  >
                    {id}
                  </span>
                ))}
              </dd>
            </div>
          )}
        </dl>
      </div>
    </div>
  );
}
