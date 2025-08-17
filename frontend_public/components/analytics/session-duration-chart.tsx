"use client"

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, CartesianGrid } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { timeRange: "0-5m", sessions: 450, avgDuration: "2m 30s" },
  { timeRange: "5-15m", sessions: 680, avgDuration: "8m 45s" },
  { timeRange: "15-30m", sessions: 520, avgDuration: "22m 15s" },
  { timeRange: "30-60m", sessions: 380, avgDuration: "45m 30s" },
  { timeRange: "1-2h", sessions: 220, avgDuration: "1h 25m" },
  { timeRange: "2h+", sessions: 150, avgDuration: "3h 10m" },
]

export function SessionDurationChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Session Duration Distribution</CardTitle>
        <CardDescription>How long users spend in your AI SaaS application per session</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{
            sessions: {
              label: "Sessions",
              color: "hsl(var(--chart-1))",
            },
          }}
          className="h-[300px]"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timeRange" />
              <YAxis />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="sessions" fill="var(--color-sessions)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
