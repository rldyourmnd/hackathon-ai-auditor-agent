import { UserSessionAnalytics } from "@/components/users/user-session-analytics"
import { UserActivityTimeline } from "@/components/users/user-activity-timeline"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Clock, Users, Activity, TrendingUp } from "lucide-react"

export default function SessionsPage() {
  const sessionStats = [
    {
      title: "Active Sessions",
      value: "1,234",
      change: "+8.2%",
      icon: Activity,
    },
    {
      title: "Avg. Session Length",
      value: "24m 32s",
      change: "+12.5%",
      icon: Clock,
    },
    {
      title: "Concurrent Users",
      value: "456",
      change: "+5.7%",
      icon: Users,
    },
    {
      title: "Session Growth",
      value: "18.7%",
      change: "+4.3%",
      icon: TrendingUp,
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">User Sessions</h1>
        <p className="text-muted-foreground">Detailed analysis of user sessions and time spent in the application.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {sessionStats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <Badge variant="default" className="text-xs">
                  {stat.change}
                </Badge>
                <span>from last week</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <UserSessionAnalytics />

      <UserActivityTimeline />
    </div>
  )
}
