"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const hours = Array.from({ length: 24 }, (_, i) => i)
const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

// Generate sample heatmap data
const generateHeatmapData = () => {
  return days.flatMap((day) =>
    hours.map((hour) => ({
      day,
      hour,
      activity: Math.floor(Math.random() * 100) + 1,
    })),
  )
}

export function UserActivityHeatmap() {
  const data = generateHeatmapData()

  const getActivityColor = (activity: number) => {
    if (activity < 20) return "bg-green-100 dark:bg-green-900/20"
    if (activity < 40) return "bg-green-200 dark:bg-green-800/40"
    if (activity < 60) return "bg-green-300 dark:bg-green-700/60"
    if (activity < 80) return "bg-green-400 dark:bg-green-600/80"
    return "bg-green-500 dark:bg-green-500"
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Activity Heatmap</CardTitle>
        <CardDescription>User activity patterns throughout the week (darker = more active)</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="grid grid-cols-25 gap-1 text-xs">
            <div></div>
            {hours.map((hour) => (
              <div key={hour} className="text-center text-muted-foreground">
                {hour % 6 === 0 ? hour : ""}
              </div>
            ))}
          </div>
          {days.map((day) => (
            <div key={day} className="grid grid-cols-25 gap-1">
              <div className="text-xs text-muted-foreground w-8">{day}</div>
              {hours.map((hour) => {
                const activity = data.find((d) => d.day === day && d.hour === hour)?.activity || 0
                return (
                  <div
                    key={`${day}-${hour}`}
                    className={`h-3 w-3 rounded-sm ${getActivityColor(activity)}`}
                    title={`${day} ${hour}:00 - ${activity}% activity`}
                  />
                )
              })}
            </div>
          ))}
        </div>
        <div className="flex items-center justify-between mt-4 text-xs text-muted-foreground">
          <span>Less active</span>
          <div className="flex space-x-1">
            <div className="h-3 w-3 rounded-sm bg-green-100 dark:bg-green-900/20"></div>
            <div className="h-3 w-3 rounded-sm bg-green-200 dark:bg-green-800/40"></div>
            <div className="h-3 w-3 rounded-sm bg-green-300 dark:bg-green-700/60"></div>
            <div className="h-3 w-3 rounded-sm bg-green-400 dark:bg-green-600/80"></div>
            <div className="h-3 w-3 rounded-sm bg-green-500 dark:bg-green-500"></div>
          </div>
          <span>More active</span>
        </div>
      </CardContent>
    </Card>
  )
}
