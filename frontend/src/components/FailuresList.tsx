import type { Diagnosis } from '../api'

const STATUS_BADGE: Record<Diagnosis['status'], string> = {
  investigating: 'bg-yellow-100 text-yellow-800',
  diagnosed: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
  resolved: 'bg-gray-100 text-gray-600',
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

interface Props {
  diagnoses: Diagnosis[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function FailuresList({ diagnoses, selectedId, onSelect }: Props) {
  if (diagnoses.length === 0) {
    return (
      <div className="text-gray-400 text-sm py-12 text-center">
        No failures yet. Trigger a DAG from the Airflow UI to get started.
      </div>
    )
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-gray-500 border-b border-gray-200">
          <th className="pb-2 font-medium">DAG</th>
          <th className="pb-2 font-medium">Task</th>
          <th className="pb-2 font-medium">Status</th>
          <th className="pb-2 font-medium">Category</th>
          <th className="pb-2 font-medium">Time</th>
        </tr>
      </thead>
      <tbody>
        {diagnoses.map((d) => (
          <tr
            key={d.id}
            onClick={() => onSelect(d.id)}
            className={`border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors ${
              selectedId === d.id ? 'bg-blue-50' : ''
            }`}
          >
            <td className="py-3 pr-4 font-mono text-xs">{d.dag_id}</td>
            <td className="py-3 pr-4 font-mono text-xs text-gray-600">{d.task_id}</td>
            <td className="py-3 pr-4">
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_BADGE[d.status]}`}>
                {d.status}
              </span>
            </td>
            <td className="py-3 pr-4 text-gray-600">{d.error_category ?? '—'}</td>
            <td className="py-3 text-gray-400">{formatTime(d.created_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
