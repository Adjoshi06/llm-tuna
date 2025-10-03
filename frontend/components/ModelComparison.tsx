'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TestExample {
  prompt: string
  base_output: string
  finetuned_output: string
  base_latency_ms: number
  finetuned_latency_ms: number
  base_tokens?: number
  finetuned_tokens?: number
}

interface Metrics {
  base_model: {
    avg_latency_ms: number
    avg_length: number
    cost_per_1m_tokens: number
  }
  finetuned_model: {
    avg_latency_ms: number
    avg_length: number
    cost_per_1m_tokens: number
  }
  improvements: {
    latency_improvement: number
    cost_improvement: number
  }
}

interface Evaluation {
  id: number
  training_job_id: number
  test_results: TestExample[]
  metrics: Metrics
  created_at: string
}

interface ModelComparisonProps {
  evaluationId: number
}

export default function ModelComparison({ evaluationId }: ModelComparisonProps) {
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [rating, setRating] = useState<{ [key: number]: 'base' | 'finetuned' }>({})

  useEffect(() => {
    fetchEvaluation()
    const interval = setInterval(fetchEvaluation, 5000) // Poll for updates
    return () => clearInterval(interval)
  }, [evaluationId])

  const fetchEvaluation = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/evaluation/${evaluationId}`)
      setEvaluation(response.data)
    } catch (error) {
      console.error('Error fetching evaluation:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRating = async (preferred: 'base' | 'finetuned') => {
    if (!evaluation) return

    try {
      await axios.post(`${API_URL}/api/evaluation/${evaluationId}/rate`, {
        evaluation_id: evaluationId,
        example_index: currentIndex,
        preferred_model: preferred,
      })
      setRating({ ...rating, [currentIndex]: preferred })
    } catch (error) {
      console.error('Error submitting rating:', error)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading evaluation...</div>
  }

  if (!evaluation || !evaluation.test_results || evaluation.test_results.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Evaluation in progress or no results yet...</p>
      </div>
    )
  }

  const currentExample = evaluation.test_results[currentIndex]
  const metrics = evaluation.metrics

  return (
    <div className="space-y-6">
      {/* Summary Metrics */}
      {metrics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Summary Metrics</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Metric</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Base Model</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fine-tuned Model</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">Avg Latency</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{metrics.base_model.avg_latency_ms}ms</td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {metrics.finetuned_model.avg_latency_ms}ms
                    {metrics.improvements.latency_improvement > 0 && (
                      <span className="ml-2 text-green-600 font-medium">
                        ({metrics.improvements.latency_improvement}% faster ⚡)
                      </span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">Cost/1M tokens</td>
                  <td className="px-4 py-3 text-sm text-gray-700">${metrics.base_model.cost_per_1m_tokens}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    ${metrics.finetuned_model.cost_per_1m_tokens}
                    {metrics.improvements.cost_improvement > 0 && (
                      <span className="ml-2 text-green-600 font-medium">
                        ({metrics.improvements.cost_improvement}% cheaper 💰)
                      </span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">Avg Length</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{metrics.base_model.avg_length} tokens</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{metrics.finetuned_model.avg_length} tokens</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Side-by-side Comparison */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Prompt:</h3>
          <div className="p-3 bg-gray-50 rounded text-sm text-gray-700">
            {currentExample.prompt}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Base Model */}
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
              <h4 className="font-semibold text-gray-900">Base Model</h4>
              <button
                onClick={() => handleRating('base')}
                className={`px-3 py-1 rounded text-sm ${
                  rating[currentIndex] === 'base'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                👍 Better
              </button>
            </div>
            <div className="mb-3 p-3 bg-gray-50 rounded text-sm text-gray-700 min-h-[200px]">
              {currentExample.base_output}
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              <div>Latency: {currentExample.base_latency_ms}ms</div>
              <div>Cost: ${((metrics?.base_model.cost_per_1m_tokens || 0) / 1000000 * (currentExample.base_tokens || 0)).toFixed(4)}</div>
            </div>
          </div>

          {/* Fine-tuned Model */}
          <div className="border rounded-lg p-4 border-primary-300">
            <div className="flex justify-between items-center mb-3">
              <h4 className="font-semibold text-primary-700">Fine-tuned Model</h4>
              <button
                onClick={() => handleRating('finetuned')}
                className={`px-3 py-1 rounded text-sm ${
                  rating[currentIndex] === 'finetuned'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                👍 Better
              </button>
            </div>
            <div className="mb-3 p-3 bg-primary-50 rounded text-sm text-gray-700 min-h-[200px]">
              {currentExample.finetuned_output}
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              <div>Latency: {currentExample.finetuned_latency_ms}ms</div>
              <div>Cost: ${((metrics?.finetuned_model.cost_per_1m_tokens || 0) / 1000000 * (currentExample.finetuned_tokens || 0)).toFixed(4)}</div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="mt-6 flex justify-between items-center">
          <button
            onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
            disabled={currentIndex === 0}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>
          <span className="text-sm text-gray-600">
            Example {currentIndex + 1} of {evaluation.test_results.length}
          </span>
          <button
            onClick={() => setCurrentIndex(Math.min(evaluation.test_results.length - 1, currentIndex + 1))}
            disabled={currentIndex === evaluation.test_results.length - 1}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  )
}

