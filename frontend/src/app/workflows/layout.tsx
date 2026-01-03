'use client'

import { Sidebar } from '@/components/sidebar'
import { usePathname } from 'next/navigation'

export default function WorkflowsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  
  // 编辑器页面路径格式: /workflows/{uuid}
  // 列表页面路径格式: /workflows
  const isEditorPage = pathname !== '/workflows' && pathname?.startsWith('/workflows/')
  
  if (isEditorPage) {
    return <>{children}</>
  }
  
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 ml-64">
        {children}
      </main>
    </div>
  )
}
