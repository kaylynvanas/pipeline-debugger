import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
})

export interface Evidence {
  source: 'airflow_logs' | 'postgres' | 'dag_source'
  content: string
}

export interface Diagnosis {
  id: string
  dag_id: string
  task_id: string
  run_id: string
  error_category: string | null
  root_cause: string | null
  evidence: Evidence[]
  suggested_fix: string | null
  status: 'investigating' | 'diagnosed' | 'error' | 'resolved'
  created_at: string
}

async function fetchDiagnoses(): Promise<Diagnosis[]> {
  const { data } = await api.get<Diagnosis[]>('/diagnoses')
  return data
}

export function useDiagnoses() {
  return useQuery({
    queryKey: ['diagnoses'],
    queryFn: fetchDiagnoses,
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 3000
      const hasInvestigating = data.some((d) => d.status === 'investigating')
      return hasInvestigating ? 3000 : false
    },
  })
}
