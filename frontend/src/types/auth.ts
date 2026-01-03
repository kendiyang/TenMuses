export interface User {
  id: string
  email: string
  username: string
  avatarUrl?: string
  role: 'user' | 'admin'
  creatorLevel: number
  createdAt: string
  updatedAt: string
}

export interface LoginInput {
  email: string
  password: string
}

export interface RegisterInput {
  email: string
  username: string
  password: string
}

export interface AuthResponse {
  user: User
  accessToken: string
  refreshToken?: string
}
