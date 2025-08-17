"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect } from "react"

interface User {
  id: string
  name: string
  email: string
  image?: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithGoogle: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session on mount
    const savedUser = localStorage.getItem("admin-user")
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (error) {
        console.error("Error parsing saved user:", error)
        localStorage.removeItem("admin-user")
      }
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    // Demo authentication - replace with real API call
    if (email === "admin@example.com" && password === "admin123") {
      const demoUser: User = {
        id: "1",
        name: "Admin User",
        email: "admin@example.com",
        image: "/admin-avatar.png",
      }
      setUser(demoUser)
      localStorage.setItem("admin-user", JSON.stringify(demoUser))
    } else {
      throw new Error("Invalid credentials")
    }
  }

  const loginWithGoogle = async () => {
    // Demo Google authentication - replace with real Google OAuth
    const googleUser: User = {
      id: "google-1",
      name: "Google Admin",
      email: "admin@google.com",
      image: "/admin-avatar.png",
    }
    setUser(googleUser)
    localStorage.setItem("admin-user", JSON.stringify(googleUser))
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem("admin-user")
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithGoogle, logout }}>{children}</AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
