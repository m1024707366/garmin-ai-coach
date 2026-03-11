interface StatCardProps {
  title: string
  value: string
  unit?: string
  onClick?: () => void
}

export default function StatCard({ title, value, unit, onClick }: StatCardProps) {
  return (
    <div 
      className={`bg-white rounded-lg shadow-md p-4 ${onClick ? 'cursor-pointer hover:shadow-lg transition-shadow' : ''}`}
      onClick={onClick}
    >
      <p className="text-gray-600 text-sm">{title}</p>
      <div className="flex items-baseline mt-1">
        <p className="text-2xl font-bold text-gray-800">{value}</p>
        {unit && <p className="text-gray-600 ml-1">{unit}</p>}
      </div>
    </div>
  )
}