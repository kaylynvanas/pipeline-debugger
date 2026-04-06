function SkeletonRow() {
  return (
    <tr className="border-b border-gray-100">
      <td className="py-3 pr-4"><div className="h-3 w-28 bg-gray-200 rounded animate-pulse" /></td>
      <td className="py-3 pr-4"><div className="h-3 w-20 bg-gray-200 rounded animate-pulse" /></td>
      <td className="py-3 pr-4"><div className="h-5 w-20 bg-gray-200 rounded-full animate-pulse" /></td>
      <td className="py-3 pr-4"><div className="h-3 w-16 bg-gray-200 rounded animate-pulse" /></td>
      <td className="py-3"><div className="h-3 w-12 bg-gray-200 rounded animate-pulse" /></td>
    </tr>
  )
}

export default function FailuresSkeleton() {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-gray-500 border-b border-gray-200">
          <th className="pb-2 font-medium">DAG</th>
          <th className="pb-2 font-medium">Task</th>
          <th className="pb-2 font-medium">Status</th>
          <th className="pb-2 font-medium">Category</th>
          <th className="pb-2 font-medium">Time</th>
        </tr>
      </thead>
      <tbody>
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
      </tbody>
    </table>
  )
}
