import * as React from "react"
import FindConnect from "./components/FindConnect"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"

function App(): React.JSX.Element {
  const [connectedPath, setConnectedPath] = React.useState<string | null>(null)
  const [isLedOn, setIsLedOn] = React.useState(false)
  const [lastSerialMessage, setLastSerialMessage] = React.useState("No serial data yet.")

  React.useEffect(() => {
    window.api.onSerialData((rawData: string) => {
      setLastSerialMessage(rawData)

      try {
        const data = JSON.parse(rawData)

        if (data.event === "led_state") {
          setIsLedOn(Boolean(data.isOn))
        }
      } catch (err) {
        console.error("Failed to parse ESP32 data:", err)
      }
    })
  }, [])

  const toggleLed = (): void => {
    window.api.sendCommand({ cmd: "toggle_led" })
  }

  return (
    <main className="container mx-auto max-w-6xl p-6 space-y-6">
      <div className="space-y-2">
        <Badge variant="outline">Electron + ESP32 command center</Badge>
        <h1 className="text-3xl font-semibold tracking-tight">ESP32 Command Center</h1>
        <p className="text-muted-foreground">
          Clean shadcn UI merged with your serial communication layer.
        </p>
      </div>

      <Separator />

      <Tabs defaultValue="device" className="space-y-6">
        <TabsList>
          <TabsTrigger value="device">Device</TabsTrigger>
          <TabsTrigger value="playground">Playground</TabsTrigger>
        </TabsList>

        <TabsContent value="device" className="space-y-6">
          <FindConnect
            connectedPath={connectedPath}
            setConnectedPath={setConnectedPath}
          />


        </TabsContent>

        <TabsContent value="playground" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>UI Playground</CardTitle>
              <CardDescription>
                Keep this tab for testing components while the device tab stays practical.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              <Button>Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="destructive">Destructive</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  )
}

export default App
