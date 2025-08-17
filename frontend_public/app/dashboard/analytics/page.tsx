import { UserEngagementChart } from "@/components/analytics/user-engagement-chart"
import { SessionDurationChart } from "@/components/analytics/session-duration-chart"
import { FeatureUsageChart } from "@/components/analytics/feature-usage-chart"
import { UserActivityHeatmap } from "@/components/analytics/user-activity-heatmap"
import { RealTimeMetrics } from "@/components/analytics/real-time-metrics"

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">User Analytics</h1>
        <p className="text-muted-foreground">Detailed analytics and insights about user behavior and engagement.</p>
      </div>

      <RealTimeMetrics />

      <div className="grid gap-6 md:grid-cols-2">
        <UserEngagementChart />
        <SessionDurationChart />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <FeatureUsageChart />
        <UserActivityHeatmap />
      </div>
    </div>
  )
}
