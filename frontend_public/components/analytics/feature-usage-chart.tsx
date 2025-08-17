"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer } from "@/components/ui/chart"

const data = [
  { name: "AI Text Generation", value: 35, color: "hsl(var(--chart-1))" },
  { name: "Image Processing", value: 25, color: "hsl(var(--chart-2))" },
  { name: "Data Analysis", value: 20, color: "hsl(var(--chart-3))" },
  { name: "API Integrations", value: 12, color: "hsl(var(--chart-4))" },
  { name: "Other Features", value: 8, color: "hsl(var(--chart-5))" },
]

export function FeatureUsageChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Feature Usage Distribution</CardTitle>
        <CardDescription>Most popular features and their usage percentages</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{
            usage: {
              label: "Usage %",
            },
          }}
          className="h-[300px]"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
