"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Clock, User, Zap, FileText, Settings } from "lucide-react"

interface ActivityEvent {
  id: string
  user: {
    name: string
    email: string
    avatar?: string
  }
  action: string
  description: string
  timestamp: string
  type: "login" | "feature" | "api" | "settings"
  duration?: string
}

const activityEvents: ActivityEvent[] = [
  {
    id: "1",
    user: {
      name: "Alice Johnson",
      email: "alice@example.com",
      avatar: "/placeholder.svg?height=32&width=32",
    },
    action: "Started AI Text Generation",
    description: "Generated 3 articles using the AI writing assistant",
    timestamp: "2 minutes ago",
    type: "feature",
    duration: "15m 32s",
  },
  {
    id: "2",
    user: {
      name: "Bob Smith",
      email: "bob@example.com",
    },
    action: "API Integration",
    description: "Made 47 API calls to the text processing endpoint",
    timestamp: "5 minutes ago",
    type: "api",
    duration: "8m 15s",
  },
  {
    id: "3",
    user: {
      name: "Carol Davis",
      email: "carol@example.com",
    },
    action: "User Login",
    description: "Logged in from Chrome on Windows",
    timestamp: "12 minutes ago",
    type: "login",
  },
  {
    id: "4",
    user: {
      name: "David Wilson",
      email: "david@example.com",
    },
    action: "Updated Settings",
    description: "Changed notification preferences and API limits",
    timestamp: "18 minutes ago",
    type: "settings",
    duration: "3m 45s",
  },
  {
    id: "5",
    user: {
      name: "Eva Martinez",
      email: "eva@example.com",
    },
    action: "Image Processing",
    description: "Processed 12 images using AI enhancement tools",
    timestamp: "25 minutes ago",
    type: "feature",
    duration: "22m 18s",
  },
]

export function UserActivityTimeline() {
  const getActivityIcon = (type: ActivityEvent["type"]) => {
    switch (type) {
      case "login":
        return <User className="h-4 w-4" />
      case "feature":
        return <Zap className="h-4 w-4" />
      case "api":
        return <FileText className="h-4 w-4" />
      case "settings":
        return <Settings className="h-4 w-4" />
    }
  }

  const getActivityColor = (type: ActivityEvent["type"]) => {
    switch (type) {
      case "login":
        return "bg-blue-500"
      case "feature":
        return "bg-green-500"
      case "api":
        return "bg-purple-500"
      case "settings":
        return "bg-orange-500"
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent User Activity</CardTitle>
        <CardDescription>Real-time user actions and time spent on different features</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activityEvents.map((event, index) => (
            <div key={event.id} className="flex items-start space-x-4">
              <div className="relative">
                <div
                  className={`w-8 h-8 rounded-full ${getActivityColor(event.type)} flex items-center justify-center text-white`}
                >
                  {getActivityIcon(event.type)}
                </div>
                {index < activityEvents.length - 1 && <div className="absolute top-8 left-4 w-px h-6 bg-border"></div>}
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Avatar className="h-6 w-6">
                      <AvatarImage src={event.user.avatar || "/placeholder.svg"} alt={event.user.name} />
                      <AvatarFallback className="text-xs">{event.user.name.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <span className="font-medium text-sm">{event.user.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {event.duration && (
                      <Badge variant="outline" className="text-xs">
                        <Clock className="mr-1 h-3 w-3" />
                        {event.duration}
                      </Badge>
                    )}
                    <span className="text-xs text-muted-foreground">{event.timestamp}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium">{event.action}</p>
                  <p className="text-xs text-muted-foreground">{event.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
