'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import axios from 'axios'
import DatasetUpload from '@/components/DatasetUpload'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Dataset {
  id: number
  name: string
  num_examples: number | null
  validation_status: string | null
  validation_report: any
  created_at: string
}

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    fetchDatasets()
  }, [])

  const fetchDatasets = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/datasets`)
      setDatasets(response.data)
    } catch (error) {
      console.error('Error fetching datasets:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this dataset?')) return

    try {
      await axios.delete(`${API_URL}/api/datasets/${id}`)
      fetchDatasets()
    } catch (error) {
      console.error('Error deleting dataset:', error)
      alert('Failed to delete dataset')
    }
  }

  const handleStartTraining = async (datasetId: number) => {
    try {
      const response = await axios.post(`${API_URL}/api/training/start`, {
        dataset_id: datasetId,
      })
      window.location.href = `/training/${response.data.id}`
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to start training')
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
              <Link href="/datasets" className="text-primary-600 font-medium">Datasets</Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Datasets</h1>
            <p className="text-gray-600 mt-1">Upload and manage your training datasets</p>
          </div>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            {showUpload ? 'Cancel' : 'Upload Dataset'}
          </button>
        </div>

        {showUpload && (
          <div className="mb-8">
            <DatasetUpload onUploadSuccess={() => {
              setShowUpload(false)
              fetchDatasets()
            }} />
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading datasets...</p>
          </div>
        ) : datasets.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500 mb-4">No datasets uploaded yet</p>
            <button
              onClick={() => setShowUpload(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Upload Your First Dataset
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Examples</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {datasets.map((dataset) => (
                  <tr key={dataset.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{dataset.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{dataset.num_examples || 0}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          dataset.validation_status === 'valid'
                            ? 'bg-green-100 text-green-800'
                            : dataset.validation_status === 'invalid'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {dataset.validation_status || 'pending'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(dataset.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      {dataset.validation_status === 'valid' && (
                        <button
                          onClick={() => handleStartTraining(dataset.id)}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          Train
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(dataset.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  )
}

