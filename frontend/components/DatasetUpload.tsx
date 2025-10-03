'use client'

import { useState, useRef } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ValidationReport {
  valid: boolean
  num_examples: number
  avg_prompt_length: number
  avg_completion_length: number
  issues: string[]
  recommendations: string[]
}

interface DatasetUploadProps {
  onUploadSuccess?: () => void
}

export default function DatasetUpload({ onUploadSuccess }: DatasetUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<any[]>([])
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return

    if (!selectedFile.name.endsWith('.jsonl')) {
      setError('File must be a .jsonl file')
      return
    }

    setFile(selectedFile)
    setError(null)
    setValidationReport(null)

    // Preview first 5 examples
    try {
      const text = await selectedFile.text()
      const lines = text.split('\n').filter(line => line.trim())
      const previewData = lines.slice(0, 5).map(line => {
        try {
          return JSON.parse(line)
        } catch {
          return null
        }
      }).filter(Boolean)
      setPreview(previewData)
    } catch (err) {
      setError('Error reading file')
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && droppedFile.name.endsWith('.jsonl')) {
      setFile(droppedFile)
      handleFileSelect({ target: { files: [droppedFile] } } as any)
    } else {
      setError('Please drop a .jsonl file')
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${API_URL}/api/datasets`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setValidationReport(response.data.validation_report)
      
      if (onUploadSuccess) {
        onUploadSuccess()
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Dataset</h2>

      <div
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition cursor-pointer"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".jsonl"
          onChange={handleFileSelect}
          className="hidden"
        />
        <div className="space-y-2">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <p className="text-gray-600">
            {file ? file.name : 'Drag and drop a JSONL file, or click to select'}
          </p>
          <p className="text-sm text-gray-500">
            Expected format: {`{"prompt": "...", "completion": "..."}`}
          </p>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      {preview.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-gray-900 mb-2">Preview (first 5 examples)</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {preview.map((example, idx) => (
              <div key={idx} className="p-2 bg-gray-50 rounded text-sm">
                <div className="font-medium">Prompt:</div>
                <div className="text-gray-700 mb-1">{example.prompt?.substring(0, 100)}...</div>
                <div className="font-medium">Completion:</div>
                <div className="text-gray-700">{example.completion?.substring(0, 100)}...</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {file && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="mt-4 w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading...' : 'Upload Dataset'}
        </button>
      )}

      {validationReport && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-900 mb-2">Validation Results</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center">
              <span className="font-medium w-32">Status:</span>
              <span
                className={`px-2 py-1 rounded ${
                  validationReport.valid
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {validationReport.valid ? 'Valid' : 'Invalid'}
              </span>
            </div>
            <div>
              <span className="font-medium w-32 inline-block">Examples:</span>
              {validationReport.num_examples}
            </div>
            <div>
              <span className="font-medium w-32 inline-block">Avg Prompt Length:</span>
              {validationReport.avg_prompt_length} tokens
            </div>
            <div>
              <span className="font-medium w-32 inline-block">Avg Completion Length:</span>
              {validationReport.avg_completion_length} tokens
            </div>
            {validationReport.issues.length > 0 && (
              <div>
                <span className="font-medium text-red-700">Issues:</span>
                <ul className="list-disc list-inside text-red-600 mt-1">
                  {validationReport.issues.slice(0, 5).map((issue, idx) => (
                    <li key={idx}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
            {validationReport.recommendations.length > 0 && (
              <div>
                <span className="font-medium text-blue-700">Recommendations:</span>
                <ul className="list-disc list-inside text-blue-600 mt-1">
                  {validationReport.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

