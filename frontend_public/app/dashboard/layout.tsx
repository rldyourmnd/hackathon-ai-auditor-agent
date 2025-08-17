import type React from "react"
import { AuthGuard } from "@/components/auth-guard"
import { DashboardSidebar } from "@/components/dashboard-sidebar"
import { DashboardHeader } from "@/components/dashboard-header"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <DashboardHeader />
        <div className="flex">
          <aside className="hidden w-64 border-r bg-background md:block">
            <DashboardSidebar />
          </aside>
          <main className="flex-1 overflow-hidden">
            <div className="container mx-auto p-6">{children}</div>
          </main>
        </div>
      </div>
    </AuthGuard>
  )
}
