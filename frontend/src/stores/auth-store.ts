import { create } from 'zustand'
import { User } from '@/types/auth'

interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: (user) => set({ user, isAuthenticated: !!user, isLoading: false }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken')
    }
    set({ user: null, isAuthenticated: false })
  },
}))
