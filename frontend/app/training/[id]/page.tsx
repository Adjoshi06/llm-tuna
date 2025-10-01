'use client'

import { useParams } from 'next/navigation'
import Link from 'next/link'
import TrainingProgress from '@/components/TrainingProgress'

export default function TrainingPage() {
  const params = useParams()
  const jobId = parseInt(params.id as string)

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
        <TrainingProgress jobId={jobId} />
      </main>
    </div>
  )
}

