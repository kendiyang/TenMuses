'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/stores/auth-store'

export default function Home() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    // 如果已登录，重定向到 workspace
    if (isAuthenticated) {
      router.push('/workspace')
    }
  }, [isAuthenticated, router])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          TenMuses
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          Build and orchestrate AI workflows with visual canvas
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/workspace"
            className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
          >
            Get Started
          </Link>
          <Link
            href="/auth/login"
            className="px-6 py-3 border border-border rounded-lg hover:bg-accent transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>
    </main>
  )
}
