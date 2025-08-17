"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, Users, Zap, Clock } from "lucide-react"

interface MetricData {
  activeUsers: number
  apiCalls: number
  avgResponseTime: number
  errorRate: number
}

export function RealTimeMetrics() {
  const [metrics, setMetrics] = useState<MetricData>({
    activeUsers: 1234,
    apiCalls: 5678,
    avgResponseTime: 245,
    errorRate: 0.12,
  })

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics((prev) => ({
        activeUsers: prev.activeUsers + Math.floor(Math.random() * 10 - 5),
        apiCalls: prev.apiCalls + Math.floor(Math.random() * 50),
        avgResponseTime: Math.max(100, prev.avgResponseTime + Math.floor(Math.random() * 20 - 10)),
        errorRate: Math.max(0, Math.min(5, prev.errorRate + (Math.random() * 0.1 - 0.05))),
      }))
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const metricsData = [
    {
      title: "Active Users",
      value: metrics.activeUsers.toLocaleString(),
      icon: Users,
      trend: "+5.2%",
      trendType: "positive" as const,
    },
    {
      title: "API Calls/min",
      value: metrics.apiCalls.toLocaleString(),
      icon: Activity,
      trend: "+12.8%",
      trendType: "positive" as const,
    },
    {
      title: "Avg Response Time",
      value: `${metrics.avgResponseTime}ms`,
      icon: Clock,
      trend: "-3.1%",
      trendType: "positive" as const,
    },
    {
      title: "Error Rate",
      value: `${metrics.errorRate.toFixed(2)}%`,
      icon: Zap,
      trend: "-0.5%",
      trendType: "positive" as const,
    },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {metricsData.map((metric) => (
        <Card key={metric.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
            <metric.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metric.value}</div>
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              <Badge variant={metric.trendType === "positive" ? "default" : "destructive"} className="text-xs">
                {metric.trend}
              </Badge>
              <span>vs last hour</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
