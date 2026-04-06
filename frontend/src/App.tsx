import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useDiagnoses } from './api'
import ErrorBoundary from './components/ErrorBoundary'
import FailuresList from './components/FailuresList'
import FailuresSkeleton from './components/FailuresSkeleton'
import DiagnosisPanel from './components/DiagnosisPanel'

function Dashboard() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { data: diagnoses = [], isLoading, isError } = useDiagnoses()

  const selected = diagnoses.find((d) => d.id === selectedId) ?? null
  const investigating = diagnoses.filter((d) => d.status === 'investigating').length

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">Pipeline Debugger</h1>
          <p className="text-xs text-gray-400">Agentic Airflow failure diagnosis</p>
        </div>
        {investigating > 0 && (
          <span className="text-xs text-yellow-600 bg-yellow-50 px-3 py-1 rounded-full border border-yellow-200 animate-pulse">
            {investigating} investigating…
          </span>
        )}
      </header>

      <div className="flex h-[calc(100vh-65px)]">
        {/* Left: failures list */}
        <div className="w-2/3 border-r border-gray-200 bg-white overflow-y-auto p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Recent failures</h2>
          {isLoading && <FailuresSkeleton />}
          {isError && <p className="text-sm text-red-500">Could not reach API.</p>}
          {!isLoading && !isError && (
            <FailuresList
              diagnoses={diagnoses}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          )}
        </div>

        {/* Right: diagnosis detail */}
        <div className="w-1/3 bg-white overflow-y-auto p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">Diagnosis</h2>
          {selected ? (
            <DiagnosisPanel diagnosis={selected} />
          ) : (
            <p className="text-sm text-gray-400">Select a failure to see the diagnosis.</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [queryClient] = useState(() => new QueryClient())
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Dashboard />
      </ErrorBoundary>
    </QueryClientProvider>
  )
}
