"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { BarChart3, Users, Activity, Settings, Menu, Home, Clock, TrendingUp, UserCheck } from "lucide-react"

const navigation = [
  {
    name: "Overview",
    href: "/dashboard",
    icon: Home,
  },
  {
    name: "User Analytics",
    href: "/dashboard/analytics",
    icon: BarChart3,
  },
  {
    name: "Active Users",
    href: "/dashboard/users",
    icon: Users,
  },
  {
    name: "Usage Metrics",
    href: "/dashboard/usage",
    icon: Activity,
  },
  {
    name: "Time Tracking",
    href: "/dashboard/time-tracking",
    icon: Clock,
  },
  {
    name: "Performance",
    href: "/dashboard/performance",
    icon: TrendingUp,
  },
  {
    name: "User Sessions",
    href: "/dashboard/sessions",
    icon: UserCheck,
  },
  {
    name: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
  },
]

interface SidebarProps {
  className?: string
}

export function DashboardSidebar({ className }: SidebarProps) {
  const pathname = usePathname()

  return (
    <div className={cn("pb-12", className)}>
      <div className="space-y-4 py-4">
        <div className="px-3 py-2">
          <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight">AI SaaS Admin</h2>
          <div className="space-y-1">
            {navigation.map((item) => (
              <Link key={item.name} href={item.href}>
                <Button variant={pathname === item.href ? "secondary" : "ghost"} className="w-full justify-start">
                  <item.icon className="mr-2 h-4 w-4" />
                  {item.name}
                </Button>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export function MobileSidebar() {
  const [open, setOpen] = useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="p-0">
        <DashboardSidebar />
      </SheetContent>
    </Sheet>
  )
}
