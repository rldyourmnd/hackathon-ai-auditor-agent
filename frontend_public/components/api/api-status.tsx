"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { RefreshCw, AlertCircle, CheckCircle, XCircle } from "lucide-react"
import { apiClient } from "@/lib/api-client"

interface ApiStatus {
  status: "online" | "offline" | "error"
  responseTime: number
  lastChecked: string
}

export function ApiStatus() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>({
    status: "offline",
    responseTime: 0,
    lastChecked: "",
  })
  const [isChecking, setIsChecking] = useState(false)

  const checkApiStatus = async () => {
    setIsChecking(true)
    const startTime = Date.now()

    try {
      await apiClient.getDashboardStats()
      const responseTime = Date.now() - startTime

      setApiStatus({
        status: "online",
        responseTime,
        lastChecked: new Date().toLocaleTimeString(),
      })
    } catch (error) {
      setApiStatus({
        status: "error",
        responseTime: 0,
        lastChecked: new Date().toLocaleTimeString(),
      })
    } finally {
      setIsChecking(false)
    }
  }

  useEffect(() => {
    checkApiStatus()
    const interval = setInterval(checkApiStatus, 60000) // Check every minute
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = () => {
    switch (apiStatus.status) {
      case "online":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "offline":
        return <XCircle className="h-4 w-4 text-gray-500" />
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />
    }
  }

  const getStatusBadge = () => {
    switch (apiStatus.status) {
      case "online":
        return (
          <Badge variant="default" className="bg-green-500">
            Online
          </Badge>
        )
      case "offline":
        return <Badge variant="secondary">Offline</Badge>
      case "error":
        return <Badge variant="destructive">Error</Badge>
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">API Status</CardTitle>
        {getStatusIcon()}
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            {getStatusBadge()}
            {apiStatus.status === "online" && (
              <p className="text-xs text-muted-foreground mt-1">Response: {apiStatus.responseTime}ms</p>
            )}
            <p className="text-xs text-muted-foreground">Last checked: {apiStatus.lastChecked}</p>
          </div>
          <Button variant="outline" size="sm" onClick={checkApiStatus} disabled={isChecking}>
            <RefreshCw className={`h-4 w-4 ${isChecking ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
