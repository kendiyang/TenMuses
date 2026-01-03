'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function TemplatesPage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to /templates/my
    router.replace('/templates/my')
  }, [router])

  return null
}
