'use client'

import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import axios from 'axios'
import ModelComparison from '@/components/ModelComparison'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function EvaluationPage() {
  const params = useParams()
  const router = useRouter()
  const trainingJobId = parseInt(params.id as string)
  const [evaluationId, setEvaluationId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    startEvaluation()
  }, [trainingJobId])

  const startEvaluation = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/evaluation/run`, {
        training_job_id: trainingJobId,
        test_size: 50,
      })
      setEvaluationId(response.data.id)
    } catch (err: any) {
      if (err.response?.status === 400 && err.response?.data?.detail?.includes('not completed')) {
        setError('Training job is not completed yet. Please wait for training to finish.')
      } else {
        setError(err.response?.data?.detail || 'Failed to start evaluation')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-xl font-bold text-gray-900">
                LLM Fine-tuning Platform
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-gray-700 hover:text-gray-900">Dashboard</Link>
              <Link href="/datasets" className="text-gray-700 hover:text-gray-900">Datasets</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Starting evaluation...</p>
          </div>
        ) : error ? (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-red-600 mb-4">{error}</div>
            <Link
              href={`/training/${trainingJobId}`}
              className="text-primary-600 hover:text-primary-700"
            >
              ← Back to Training Job
            </Link>
          </div>
        ) : evaluationId ? (
          <ModelComparison evaluationId={evaluationId} />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">No evaluation found</p>
          </div>
        )}
      </main>
    </div>
  )
}

