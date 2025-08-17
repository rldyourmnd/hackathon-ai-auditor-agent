import { ApiStatus } from "@/components/api/api-status"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Configure your admin panel and API connections.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <ApiStatus />

        <Card>
          <CardHeader>
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>Configure your Python backend API connection</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="api-url">API Base URL</Label>
              <Input
                id="api-url"
                placeholder="http://localhost:8000"
                defaultValue={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="api-key">API Key</Label>
              <Input id="api-key" type="password" placeholder="Your API key" />
            </div>
            <Button className="w-full">Save Configuration</Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Environment Variables</CardTitle>
          <CardDescription>Required environment variables for API integration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label className="text-sm font-medium">NEXT_PUBLIC_API_URL</Label>
                <p className="text-xs text-muted-foreground">Base URL for your Python API</p>
                <code className="text-xs bg-muted px-2 py-1 rounded">http://localhost:8000</code>
              </div>
              <div>
                <Label className="text-sm font-medium">API_SECRET_KEY</Label>
                <p className="text-xs text-muted-foreground">Secret key for API authentication</p>
                <code className="text-xs bg-muted px-2 py-1 rounded">your-secret-key</code>
              </div>
            </div>

            <Separator />

            <div>
              <h4 className="text-sm font-medium mb-2">Python Backend Requirements</h4>
              <div className="text-xs text-muted-foreground space-y-1">
                <p>• FastAPI or Flask backend running on port 8000</p>
                <p>• CORS enabled for your frontend domain</p>
                <p>• JWT authentication for admin endpoints</p>
                <p>• Endpoints matching the API client structure</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
