'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TrainingJob {
  id: number
  dataset_id: number
  status: string
  config: any
  model_path: string | null
  training_logs: Array<{ step: number; loss: number; epoch: number; timestamp: string }> | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

interface TrainingProgressProps {
  jobId: number
}

export default function TrainingProgress({ jobId }: TrainingProgressProps) {
  const [job, setJob] = useState<TrainingJob | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchJob()
    const interval = setInterval(fetchJob, 2000) // Poll every 2 seconds
    return () => clearInterval(interval)
  }, [jobId])

  const fetchJob = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/training/${jobId}`)
      setJob(response.data)
    } catch (error) {
      console.error('Error fetching training job:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  if (!job) {
    return <div className="text-center py-8 text-red-600">Training job not found</div>
  }

  const logs = job.training_logs || []
  const chartData = logs.map(log => ({
    step: log.step,
    loss: log.loss,
  }))

  const latestLog = logs[logs.length - 1]
  const totalSteps = job.config?.num_epochs ? logs.length : 0

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Training Job #{job.id}</h2>
            <p className="text-sm text-gray-500">Dataset ID: {job.dataset_id}</p>
          </div>
          <span
            className={`px-3 py-1 rounded text-sm font-medium ${
              job.status === 'completed'
                ? 'bg-green-100 text-green-800'
                : job.status === 'training'
                ? 'bg-blue-100 text-blue-800'
                : job.status === 'failed'
                ? 'bg-red-100 text-red-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {job.status}
          </span>
        </div>

        {job.error_message && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
            <strong>Error:</strong> {job.error_message}
          </div>
        )}

        {job.status === 'training' && latestLog && (
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-500">Current Step</div>
              <div className="text-lg font-semibold">{latestLog.step}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Current Loss</div>
              <div className="text-lg font-semibold">{latestLog.loss.toFixed(4)}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Epoch</div>
              <div className="text-lg font-semibold">{latestLog.epoch.toFixed(2)}</div>
            </div>
          </div>
        )}

        {job.started_at && (
          <div className="mt-4 text-sm text-gray-500">
            Started: {new Date(job.started_at).toLocaleString()}
          </div>
        )}

        {job.completed_at && (
          <div className="mt-2 text-sm text-gray-500">
            Completed: {new Date(job.completed_at).toLocaleString()}
          </div>
        )}
      </div>

      {/* Loss Chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Training Loss</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="step" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="loss" stroke="#0ea5e9" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Actions */}
      {job.status === 'completed' && job.model_path && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Next Steps</h3>
          <div className="space-y-2">
            <a
              href={`/evaluation/${job.id}`}
              className="block px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-center"
            >
              Evaluate Model
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

