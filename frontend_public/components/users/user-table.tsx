"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { MoreHorizontal, Search, Eye, Ban, Mail } from "lucide-react"

interface User {
  id: string
  name: string
  email: string
  avatar?: string
  status: "active" | "inactive" | "suspended"
  lastActive: string
  totalSessions: number
  avgSessionTime: string
  apiCalls: number
  plan: "free" | "pro" | "enterprise"
  joinDate: string
}

const mockUsers: User[] = [
  {
    id: "1",
    name: "Alice Johnson",
    email: "alice@example.com",
    avatar: "/placeholder.svg?height=32&width=32",
    status: "active",
    lastActive: "2 minutes ago",
    totalSessions: 145,
    avgSessionTime: "24m 32s",
    apiCalls: 2847,
    plan: "pro",
    joinDate: "2024-01-15",
  },
  {
    id: "2",
    name: "Bob Smith",
    email: "bob@example.com",
    status: "active",
    lastActive: "1 hour ago",
    totalSessions: 89,
    avgSessionTime: "18m 45s",
    apiCalls: 1523,
    plan: "free",
    joinDate: "2024-02-03",
  },
  {
    id: "3",
    name: "Carol Davis",
    email: "carol@example.com",
    status: "inactive",
    lastActive: "3 days ago",
    totalSessions: 234,
    avgSessionTime: "31m 12s",
    apiCalls: 4521,
    plan: "enterprise",
    joinDate: "2023-11-22",
  },
  {
    id: "4",
    name: "David Wilson",
    email: "david@example.com",
    status: "suspended",
    lastActive: "1 week ago",
    totalSessions: 67,
    avgSessionTime: "15m 23s",
    apiCalls: 892,
    plan: "free",
    joinDate: "2024-03-10",
  },
  {
    id: "5",
    name: "Eva Martinez",
    email: "eva@example.com",
    status: "active",
    lastActive: "30 minutes ago",
    totalSessions: 178,
    avgSessionTime: "27m 18s",
    apiCalls: 3245,
    plan: "pro",
    joinDate: "2024-01-08",
  },
]

export function UserTable() {
  const [searchTerm, setSearchTerm] = useState("")
  const [users] = useState<User[]>(mockUsers)

  const filteredUsers = users.filter(
    (user) =>
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const getStatusBadge = (status: User["status"]) => {
    switch (status) {
      case "active":
        return <Badge variant="default">Active</Badge>
      case "inactive":
        return <Badge variant="secondary">Inactive</Badge>
      case "suspended":
        return <Badge variant="destructive">Suspended</Badge>
    }
  }

  const getPlanBadge = (plan: User["plan"]) => {
    switch (plan) {
      case "free":
        return <Badge variant="outline">Free</Badge>
      case "pro":
        return <Badge variant="default">Pro</Badge>
      case "enterprise":
        return <Badge variant="secondary">Enterprise</Badge>
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Plan</TableHead>
              <TableHead>Last Active</TableHead>
              <TableHead>Sessions</TableHead>
              <TableHead>Avg. Time</TableHead>
              <TableHead>API Calls</TableHead>
              <TableHead className="w-[70px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredUsers.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={user.avatar || "/placeholder.svg"} alt={user.name} />
                      <AvatarFallback>{user.name.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="font-medium">{user.name}</div>
                      <div className="text-sm text-muted-foreground">{user.email}</div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>{getStatusBadge(user.status)}</TableCell>
                <TableCell>{getPlanBadge(user.plan)}</TableCell>
                <TableCell className="text-sm">{user.lastActive}</TableCell>
                <TableCell>{user.totalSessions}</TableCell>
                <TableCell>{user.avgSessionTime}</TableCell>
                <TableCell>{user.apiCalls.toLocaleString()}</TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuItem>
                        <Eye className="mr-2 h-4 w-4" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Mail className="mr-2 h-4 w-4" />
                        Send Message
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-red-600">
                        <Ban className="mr-2 h-4 w-4" />
                        Suspend User
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
