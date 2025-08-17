import { UserTable } from "@/components/users/user-table"
import { UserEngagementMetrics } from "@/components/users/user-engagement-metrics"
import { UserActivityTimeline } from "@/components/users/user-activity-timeline"

export default function UsersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Active Users</h1>
        <p className="text-muted-foreground">Monitor and manage active users across your AI SaaS platform.</p>
      </div>

      <UserEngagementMetrics />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <UserTable />
        </div>
        <div>
          <UserActivityTimeline />
        </div>
      </div>
    </div>
  )
}
