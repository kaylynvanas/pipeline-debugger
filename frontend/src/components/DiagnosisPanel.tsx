import { type ReactNode } from 'react'
import type { Diagnosis } from '../api'

const SOURCE_LABEL: Record<string, string> = {
  airflow_logs: 'Airflow logs',
  postgres: 'Postgres',
  dag_source: 'DAG source',
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <div className="text-sm text-gray-800 leading-relaxed">{children}</div>
    </div>
  )
}

interface Props {
  diagnosis: Diagnosis
}

export default function DiagnosisPanel({ diagnosis: d }: Props) {
  return (
    <div className="space-y-6">
      <Field label="DAG / Task">
        <span className="font-mono">
          {d.dag_id} <span className="text-gray-400">/</span> {d.task_id}
        </span>
      </Field>

      {d.error_category && (
        <Field label="Category">
          <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">{d.error_category}</span>
        </Field>
      )}

      {d.root_cause ? (
        <Field label="Root cause">{d.root_cause}</Field>
      ) : (
        <div className="text-sm text-yellow-600 animate-pulse">Investigating…</div>
      )}

      {d.evidence.length > 0 && (
        <Field label="Evidence">
          <div className="space-y-3 mt-1">
            {d.evidence.map((e) => (
              <div key={e.source} className="rounded border border-gray-200">
                <div className="px-3 py-1 bg-gray-50 text-xs text-gray-500 border-b border-gray-200 rounded-t">
                  {SOURCE_LABEL[e.source] ?? e.source}
                </div>
                <pre className="px-3 py-2 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap break-words max-h-48">
                  {e.content}
                </pre>
              </div>
            ))}
          </div>
        </Field>
      )}

      {d.suggested_fix && (
        <Field label="Suggested fix">{d.suggested_fix}</Field>
      )}
    </div>
  )
}
