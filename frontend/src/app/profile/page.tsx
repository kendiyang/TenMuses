'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { User, FileText, BarChart3, Heart, LogOut, Settings } from 'lucide-react'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth-store'
import AvatarUpload from '@/components/avatar/AvatarUpload'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface UserStats {
  total_workflows: number
  total_runs: number
  total_templates_published: number
  total_favorites: number
  most_used_template_id?: string
  last_run_at?: string
}

export default function ProfilePage() {
  const router = useRouter()
  const { isAuthenticated, user, logout } = useAuthStore()
  const [stats, setStats] = useState<UserStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    loadStats()
  }, [isAuthenticated, router])

  const loadStats = async () => {
    try {
      setIsLoading(true)
      const token = localStorage.getItem('accessToken')
      if (!token) throw new Error('No access token found')

      const response = await axios.get(
        `${API_URL}/api/v1/users/me/statistics`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setStats(response.data)
    } catch (error) {
      console.error('Failed to load statistics:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    router.push('/auth/login')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading profile...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Profile</h1>
            <p className="text-muted-foreground">Manage your account and view your statistics</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Sidebar */}
          <div className="md:col-span-1">
            {/* Profile Card */}
            <div className="bg-accent/50 rounded-xl p-6 mb-6">
              <AvatarUpload
                currentAvatarUrl={user?.avatar_url}
                onUploadSuccess={(url) => {
                  // 更新本地用户状态（可选）
                  console.log('Avatar updated:', url)
                }}
                className="mb-4"
              />
              <h2 className="text-2xl font-bold mb-1 text-center">{user?.username || 'User'}</h2>
              <p className="text-sm text-muted-foreground mb-4 text-center">{user?.email || 'No email'}</p>
              <button className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-accent">
                <Settings className="w-4 h-4" />
                Edit Profile
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="space-y-2">
              <button
                onClick={() => setActiveTab('overview')}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  activeTab === 'overview'
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  activeTab === 'settings'
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                Settings
              </button>
            </div>
          </div>

          {/* Main Content */}
          <div className="md:col-span-2">
            {activeTab === 'overview' && stats && (
              <div className="space-y-6">
                {/* Statistics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-accent/50 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="p-2 bg-blue-500/20 rounded-lg">
                        <FileText className="w-5 h-5 text-blue-600" />
                      </div>
                      <h3 className="text-sm font-medium text-muted-foreground">Total Workflows</h3>
                    </div>
                    <p className="text-3xl font-bold">{stats.total_workflows}</p>
                  </div>

                  <div className="bg-accent/50 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="p-2 bg-green-500/20 rounded-lg">
                        <BarChart3 className="w-5 h-5 text-green-600" />
                      </div>
                      <h3 className="text-sm font-medium text-muted-foreground">Total Runs</h3>
                    </div>
                    <p className="text-3xl font-bold">{stats.total_runs}</p>
                  </div>

                  <div className="bg-accent/50 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="p-2 bg-purple-500/20 rounded-lg">
                        <FileText className="w-5 h-5 text-purple-600" />
                      </div>
                      <h3 className="text-sm font-medium text-muted-foreground">Templates Published</h3>
                    </div>
                    <p className="text-3xl font-bold">{stats.total_templates_published}</p>
                  </div>

                  <div className="bg-accent/50 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="p-2 bg-red-500/20 rounded-lg">
                        <Heart className="w-5 h-5 text-red-600" />
                      </div>
                      <h3 className="text-sm font-medium text-muted-foreground">Favorited Templates</h3>
                    </div>
                    <p className="text-3xl font-bold">{stats.total_favorites}</p>
                  </div>
                </div>

                {/* Additional Info */}
                <div className="bg-accent/50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold mb-4">Activity</h3>
                  <div className="space-y-3">
                    {stats.last_run_at ? (
                      <div>
                        <p className="text-sm text-muted-foreground">Last Activity</p>
                        <p className="font-medium">
                          {new Date(stats.last_run_at).toLocaleString()}
                        </p>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No activity yet</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6">
                <div className="bg-accent/50 rounded-xl p-6">
                  <h3 className="text-lg font-semibold mb-4">Account Settings</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium block mb-2">Email</label>
                      <input
                        type="email"
                        value={user?.email || ''}
                        disabled
                        className="w-full px-4 py-2 bg-background border border-border rounded-lg disabled:opacity-50"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium block mb-2">Username</label>
                      <input
                        type="text"
                        value={user?.username || ''}
                        disabled
                        className="w-full px-4 py-2 bg-background border border-border rounded-lg disabled:opacity-50"
                      />
                    </div>
                    <button className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90">
                      Update Settings
                    </button>
                  </div>
                </div>

                <div className="bg-accent/50 rounded-xl p-6 border border-destructive/20">
                  <h3 className="text-lg font-semibold text-destructive mb-4">Danger Zone</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Delete your account and all associated data. This action cannot be undone.
                  </p>
                  <button className="px-6 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90">
                    Delete Account
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
