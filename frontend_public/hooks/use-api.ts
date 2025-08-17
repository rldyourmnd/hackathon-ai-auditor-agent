"use client"

import { useState, useEffect, useCallback } from "react"
import { apiClient, ApiError } from "@/lib/api-client"

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

interface UseApiOptions {
  immediate?: boolean
  onSuccess?: (data: any) => void
  onError?: (error: ApiError) => void
}

export function useApi<T>(apiCall: () => Promise<{ data: T; success: boolean }>, options: UseApiOptions = {}) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: options.immediate !== false,
    error: null,
  })

  const execute = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const response = await apiCall()
      setState({
        data: response.data,
        loading: false,
        error: null,
      })
      options.onSuccess?.(response.data)
    } catch (error) {
      const errorMessage = error instanceof ApiError ? error.message : "An unexpected error occurred"
      setState({
        data: null,
        loading: false,
        error: errorMessage,
      })
      options.onError?.(error as ApiError)
    }
  }, [apiCall, options])

  useEffect(() => {
    if (options.immediate !== false) {
      execute()
    }
  }, [execute, options.immediate])

  const refetch = useCallback(() => {
    execute()
  }, [execute])

  return {
    ...state,
    refetch,
    execute,
  }
}

// Specific hooks for common API calls
export function useUsers(params?: { page?: number; limit?: number; search?: string }) {
  return useApi(() => apiClient.getUsers(params))
}

export function useAnalytics(timeRange = "7d") {
  return useApi(() => apiClient.getAnalytics(timeRange))
}

export function useUserEngagement(timeRange = "7d") {
  return useApi(() => apiClient.getUserEngagement(timeRange))
}

export function useSessionAnalytics(timeRange = "24h") {
  return useApi(() => apiClient.getSessionAnalytics(timeRange))
}

export function useFeatureUsage(timeRange = "7d") {
  return useApi(() => apiClient.getFeatureUsage(timeRange))
}

export function useRealTimeMetrics() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await apiClient.getRealTimeMetrics()
        setData(response.data)
        setError(null)
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to fetch metrics")
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [])

  return { data, loading, error }
}

export function useUserActivity(params?: { page?: number; limit?: number; userId?: string }) {
  return useApi(() => apiClient.getUserActivity(params))
}

export function useDashboardStats() {
  return useApi(() => apiClient.getDashboardStats())
}
