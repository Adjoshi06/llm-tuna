'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Dataset {
  id: number
  name: string
  num_examples: number | null
  validation_status: string | null
  created_at: string
}

interface TrainingJob {
  id: number
  dataset_id: number
  status: string
  started_at: string | null
  completed_at: string | null
}

export default function Dashboard() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [trainingJobs, setTrainingJobs] = useState<TrainingJob[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [datasetsRes, trainingRes] = await Promise.all([
        axios.get(`${API_URL}/api/datasets`),
        axios.get(`${API_URL}/api/training`)
      ])
      setDatasets(datasetsRes.data)
      setTrainingJobs(trainingRes.data || [])
    } catch (error) {
      console.error('Error fetching data:', error)
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
              <h1 className="text-xl font-bold text-gray-900">LLM Fine-tuning Platform</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/" className="text-gray-700 hover:text-gray-900">Dashboard</Link>
              <Link href="/datasets" className="text-gray-700 hover:text-gray-900">Datasets</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h2>
          <p className="text-gray-600">Manage your datasets and training jobs</p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Datasets Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Datasets</h3>
                <Link
                  href="/datasets"
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  View All →
                </Link>
              </div>
              <div className="space-y-3">
                {datasets.length === 0 ? (
                  <p className="text-gray-500 text-sm">No datasets uploaded yet</p>
                ) : (
                  datasets.slice(0, 5).map((dataset) => (
                    <div key={dataset.id} className="border-b pb-2 last:border-0">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium text-gray-900">{dataset.name}</p>
                          <p className="text-sm text-gray-500">
                            {dataset.num_examples || 0} examples
                          </p>
                        </div>
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            dataset.validation_status === 'valid'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {dataset.validation_status || 'pending'}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Training Jobs Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Training Jobs</h3>
              </div>
              <div className="space-y-3">
                {trainingJobs.length === 0 ? (
                  <p className="text-gray-500 text-sm">No training jobs yet</p>
                ) : (
                  trainingJobs.slice(0, 5).map((job) => (
                    <div key={job.id} className="border-b pb-2 last:border-0">
                      <div className="flex justify-between items-start">
                        <div>
                          <Link
                            href={`/training/${job.id}`}
                            className="font-medium text-primary-600 hover:text-primary-700"
                          >
                            Job #{job.id}
                          </Link>
                          <p className="text-sm text-gray-500">
                            Dataset ID: {job.dataset_id}
                          </p>
                        </div>
                        <span
                          className={`px-2 py-1 text-xs rounded ${
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
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/datasets"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
            >
              Upload Dataset
            </Link>
          </div>
        </div>
      </main>
    </div>
  )
}

