"use client"

import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, CartesianGrid } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Badge } from "@/components/ui/badge"

const sessionData = [
  { time: "00:00", sessions: 45, avgDuration: 12 },
  { time: "02:00", sessions: 23, avgDuration: 8 },
  { time: "04:00", sessions: 12, avgDuration: 6 },
  { time: "06:00", sessions: 34, avgDuration: 15 },
  { time: "08:00", sessions: 89, avgDuration: 22 },
  { time: "10:00", sessions: 156, avgDuration: 28 },
  { time: "12:00", sessions: 198, avgDuration: 32 },
  { time: "14:00", sessions: 234, avgDuration: 35 },
  { time: "16:00", sessions: 267, avgDuration: 38 },
  { time: "18:00", sessions: 189, avgDuration: 29 },
  { time: "20:00", sessions: 134, avgDuration: 25 },
  { time: "22:00", sessions: 78, avgDuration: 18 },
]

const topFeatures = [
  { name: "AI Text Generation", usage: 85, timeSpent: "45m 32s" },
  { name: "Image Processing", usage: 72, timeSpent: "32m 18s" },
  { name: "Data Analysis", usage: 68, timeSpent: "28m 45s" },
  { name: "API Integration", usage: 54, timeSpent: "22m 12s" },
  { name: "Report Generation", usage: 41, timeSpent: "18m 36s" },
]

export function UserSessionAnalytics() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Session Activity by Hour</CardTitle>
          <CardDescription>User sessions and average duration throughout the day</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={{
              sessions: {
                label: "Sessions",
                color: "hsl(var(--chart-1))",
              },
              avgDuration: {
                label: "Avg Duration (min)",
                color: "hsl(var(--chart-2))",
              },
            }}
            className="h-[300px]"
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sessionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  type="monotone"
                  dataKey="sessions"
                  stroke="var(--color-sessions)"
                  strokeWidth={2}
                  dot={{ fill: "var(--color-sessions)" }}
                />
                <Line
                  type="monotone"
                  dataKey="avgDuration"
                  stroke="var(--color-avgDuration)"
                  strokeWidth={2}
                  dot={{ fill: "var(--color-avgDuration)" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top Features by Time Spent</CardTitle>
          <CardDescription>Most used features and average time users spend on each</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {topFeatures.map((feature, index) => (
              <div key={feature.name} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium text-sm">{feature.name}</p>
                    <p className="text-xs text-muted-foreground">{feature.usage}% of users</p>
                  </div>
                </div>
                <Badge variant="outline">{feature.timeSpent}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
