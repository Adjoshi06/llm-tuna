'use client'

interface MetricsCardProps {
  title: string
  value: string | number
  subtitle?: string
  improvement?: number
  icon?: React.ReactNode
}

export default function MetricsCard({ title, value, subtitle, improvement, icon }: MetricsCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
          {improvement !== undefined && improvement > 0 && (
            <p className="text-sm text-green-600 mt-1 font-medium">
              {improvement}% improvement
            </p>
          )}
        </div>
        {icon && <div className="text-primary-600">{icon}</div>}
      </div>
    </div>
  )
}

