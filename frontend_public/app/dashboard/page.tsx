"use client"

import { useAuth } from "@/components/auth-provider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Users, Activity, Clock, TrendingUp } from "lucide-react"
import { RealTimeMetrics } from "@/components/analytics/real-time-metrics"
import { UserEngagementChart } from "@/components/analytics/user-engagement-chart"
import { FeatureUsageChart } from "@/components/analytics/feature-usage-chart"

export default function DashboardPage() {
  const { user } = useAuth()

  const stats = [
    {
      title: "Total Users",
      value: "2,847",
      change: "+12.5%",
      changeType: "positive" as const,
      icon: Users,
    },
    {
      title: "Active Sessions",
      value: "1,234",
      change: "+8.2%",
      changeType: "positive" as const,
      icon: Activity,
    },
    {
      title: "Avg. Session Time",
      value: "24m 32s",
      change: "-2.1%",
      changeType: "negative" as const,
      icon: Clock,
    },
    {
      title: "Growth Rate",
      value: "18.7%",
      change: "+4.3%",
      changeType: "positive" as const,
      icon: TrendingUp,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard Overview</h1>
        <p className="text-muted-foreground">
          Welcome back, {user?.name}. Here's what's happening with your AI SaaS platform.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <Badge variant={stat.changeType === "positive" ? "default" : "destructive"} className="text-xs">
                  {stat.change}
                </Badge>
                <span>from last month</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">Real-Time Metrics</h2>
        <RealTimeMetrics />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <UserEngagementChart />
        <FeatureUsageChart />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest user actions and system events</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium">New user registration</p>
                <p className="text-xs text-muted-foreground">2 minutes ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium">API usage spike detected</p>
                <p className="text-xs text-muted-foreground">5 minutes ago</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium">System maintenance completed</p>
                <p className="text-xs text-muted-foreground">1 hour ago</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
