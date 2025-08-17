"use client"

import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis, CartesianGrid } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { date: "2024-01-01", activeUsers: 1200, newUsers: 80, sessions: 1800 },
  { date: "2024-01-02", activeUsers: 1350, newUsers: 120, sessions: 2100 },
  { date: "2024-01-03", activeUsers: 1180, newUsers: 90, sessions: 1950 },
  { date: "2024-01-04", activeUsers: 1420, newUsers: 150, sessions: 2300 },
  { date: "2024-01-05", activeUsers: 1680, newUsers: 200, sessions: 2800 },
  { date: "2024-01-06", activeUsers: 1550, newUsers: 180, sessions: 2600 },
  { date: "2024-01-07", activeUsers: 1750, newUsers: 220, sessions: 3000 },
  { date: "2024-01-08", activeUsers: 1620, newUsers: 190, sessions: 2700 },
  { date: "2024-01-09", activeUsers: 1890, newUsers: 250, sessions: 3200 },
  { date: "2024-01-10", activeUsers: 2100, newUsers: 300, sessions: 3500 },
  { date: "2024-01-11", activeUsers: 1980, newUsers: 280, sessions: 3300 },
  { date: "2024-01-12", activeUsers: 2200, newUsers: 320, sessions: 3700 },
  { date: "2024-01-13", activeUsers: 2050, newUsers: 290, sessions: 3400 },
  { date: "2024-01-14", activeUsers: 2300, newUsers: 350, sessions: 3900 },
]

export function UserEngagementChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>User Engagement Trends</CardTitle>
        <CardDescription>
          Daily active users, new registrations, and session counts over the last 14 days
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{
            activeUsers: {
              label: "Active Users",
              color: "hsl(var(--chart-1))",
            },
            newUsers: {
              label: "New Users",
              color: "hsl(var(--chart-2))",
            },
            sessions: {
              label: "Sessions",
              color: "hsl(var(--chart-3))",
            },
          }}
          className="h-[300px]"
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                }
              />
              <YAxis />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Area
                type="monotone"
                dataKey="activeUsers"
                stackId="1"
                stroke="var(--color-activeUsers)"
                fill="var(--color-activeUsers)"
                fillOpacity={0.6}
              />
              <Area
                type="monotone"
                dataKey="newUsers"
                stackId="2"
                stroke="var(--color-newUsers)"
                fill="var(--color-newUsers)"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
