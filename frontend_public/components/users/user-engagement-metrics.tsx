"use client"

import type React from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, Clock, Zap, Target, Users } from "lucide-react"

interface EngagementMetric {
  title: string
  value: string
  progress: number
  trend: string
  trendDirection: "up" | "down"
  icon: React.ElementType
  description: string
}

const engagementMetrics: EngagementMetric[] = [
  {
    title: "Daily Active Users",
    value: "1,234",
    progress: 78,
    trend: "+12.5%",
    trendDirection: "up",
    icon: Users,
    description: "Users active in the last 24 hours",
  },
  {
    title: "Session Engagement",
    value: "85.2%",
    progress: 85,
    trend: "+3.2%",
    trendDirection: "up",
    icon: Target,
    description: "Percentage of engaged sessions",
  },
  {
    title: "Feature Adoption",
    value: "67.8%",
    progress: 68,
    trend: "-2.1%",
    trendDirection: "down",
    icon: Zap,
    description: "Users trying new features",
  },
  {
    title: "Avg. Session Duration",
    value: "24m 32s",
    progress: 72,
    trend: "+8.7%",
    trendDirection: "up",
    icon: Clock,
    description: "Average time spent per session",
  },
]

export function UserEngagementMetrics() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {engagementMetrics.map((metric) => (
        <Card key={metric.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
            <metric.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metric.value}</div>
            <div className="flex items-center space-x-2 mt-2">
              <Badge variant={metric.trendDirection === "up" ? "default" : "destructive"} className="text-xs">
                {metric.trendDirection === "up" ? (
                  <TrendingUp className="mr-1 h-3 w-3" />
                ) : (
                  <TrendingDown className="mr-1 h-3 w-3" />
                )}
                {metric.trend}
              </Badge>
            </div>
            <Progress value={metric.progress} className="mt-3" />
            <p className="text-xs text-muted-foreground mt-2">{metric.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
