import * as React from "react"
import FindConnect from "./components/FindConnect"

import { useRuntimeStore } from './zustand/RuntimeStore'

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"

import { Activity, Boxes, Cpu, PlugZap, TerminalSquare } from "lucide-react"

type IncomingPacket = {
  kind: string
  id: string
  moduleType: string
  payload: Record<string, any>
}

function App(): React.JSX.Element {
  const [connectedPath, setConnectedPath] = React.useState<string | null>(null)
  const [lastSerialMessage, setLastSerialMessage] = React.useState("No serial data yet.")
  const [lastPacket, setLastPacket] = React.useState<IncomingPacket | null>(null)

  const modules = useRuntimeStore((state) => state.modules)
  const registerModule = useRuntimeStore((state) => state.registerModule)
  const patchModuleState = useRuntimeStore((state) => state.patchModuleState)
  const removeModule = useRuntimeStore((state) => state.removeModule)

  React.useEffect(() => {
    let didInit = false

    const initConnection = async () => {
      if (didInit) return
      didInit = true

      try {
        const result = await window.api.autoConnect()
        if (result.ok && result.path) {
          setConnectedPath(result.path)
          window.api.sendCommand({ cmd: "re-register" })
        }
      } catch (err) {
        console.error("[APP] autoConnect failed:", err)
      }
    }

    void initConnection()
  }, [])

  React.useEffect(() => {
    window.api.onSerialData((rawData: string) => {
      setLastSerialMessage(rawData)

      try {
        const data = JSON.parse(rawData) as IncomingPacket
        setLastPacket(data)

        if (!data.id || !data.moduleType) {
          return
        }

        const kind = typeof data.kind === "string" ? data.kind.toLowerCase() : data.kind

        // REGISTER
        if (kind === "register") {
          registerModule({
            id: data.id,
            moduleType: data.moduleType,
            connected: true,
            payload: data.payload ?? {},
          })
          return
        }

        // STATE
        if (kind === "state") {
          const existing = modules[data.id]

          if (!existing) {
            registerModule({
              id: data.id,
              moduleType: data.moduleType,
              connected: true,
              payload: data.payload ?? {},
            })
            return
          }

          patchModuleState(data.id, data.payload ?? {})
          return
        }

        // REMOVE / DISCONNECT
        if (kind === "remove" || kind === "disconnect") {
          removeModule(data.id)
        }
        if (kind === "log") {
          setLastSerialMessage(data.payload.message ?? "")
          console.log(`[MODULE ${data.moduleType === "101 ?" ? "Log ?" : data.moduleType}]`, data.payload)


        }
      } catch (err) {
        console.error("[RENDERER] parse failed:", err)
      }
    })
  }, [modules, patchModuleState, registerModule, removeModule])

  const sendReregister = (): void => {
    window.api.sendCommand({ cmd: "re-register" })
  }

  const toggleLed = (): void => {
    window.api.sendCommand({ cmd: "toggle_led" })
  }

  const moduleList = React.useMemo(() => Object.values(modules), [modules])

  const totalModules = moduleList.length
  const connectedModules = moduleList.filter((module) => module.connected).length

  const kindLabel = React.useMemo(() => {
    if (lastPacket?.kind === undefined || lastPacket?.kind === null) return "Unknown"

    if (typeof lastPacket.kind === "string") return lastPacket.kind

    switch (lastPacket.kind) {
      case 0:
        return "REGISTER"
      case 1:
        return "STATE"
      case 2:
        return "COMMAND"
      default:
        return `KIND ${lastPacket.kind}`
    }
  }, [lastPacket])

  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto max-w-7xl space-y-6 p-6">
        <section className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-3">
              <Badge variant="outline" className="gap-2">
                <Activity className="h-3.5 w-3.5" />
                Runtime Dashboard
              </Badge>

              <div className="space-y-2">
                <h1 className="text-3xl font-semibold tracking-tight">
                  ESP32 Command Center
                </h1>
                <p className="max-w-2xl text-sm text-muted-foreground md:text-base">
                  Your first page now reads from the runtime registry instead of local
                  component state.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={sendReregister}>
                Re-register Modules
              </Button>
              <Button onClick={toggleLed}>Toggle LED</Button>
            </div>
          </div>

          <Separator />

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Connection</CardDescription>
                <CardTitle className="flex items-center gap-2 text-base">
                  <PlugZap className="h-4 w-4" />
                  Device Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Badge variant={connectedPath ? "default" : "secondary"}>
                  {connectedPath ? "Connected" : "Disconnected"}
                </Badge>
                <p className="break-all text-sm text-muted-foreground">
                  {connectedPath ?? "No serial path connected yet."}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Runtime</CardDescription>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Boxes className="h-4 w-4" />
                  Registered Modules
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-2xl font-semibold">{totalModules}</div>
                <p className="text-sm text-muted-foreground">
                  {connectedModules} connected in runtime store
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Protocol</CardDescription>
                <CardTitle className="text-base">Last Packet Kind</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Badge variant="outline">{kindLabel}</Badge>
                <p className="text-sm text-muted-foreground">
                  {lastPacket?.moduleType
                    ? `Module type: ${lastPacket.moduleType}`
                    : "Waiting for incoming packets"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Serial Layer</CardDescription>
                <CardTitle className="flex items-center gap-2 text-base">
                  <TerminalSquare className="h-4 w-4" />
                  Last Raw Message
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="line-clamp-3 text-sm text-muted-foreground">
                  {lastSerialMessage}
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList>
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="modules">Modules</TabsTrigger>
            <TabsTrigger value="serial">Serial Inspector</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
              <FindConnect
                connectedPath={connectedPath}
                setConnectedPath={setConnectedPath}
              />

              <Card>
                <CardHeader>
                  <CardTitle>Runtime Summary</CardTitle>
                  <CardDescription>
                    Live information coming from your Zustand runtime store.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {moduleList.length === 0 ? (
                    <div className="rounded-lg border p-4 text-sm text-muted-foreground">
                      No modules registered yet. Connect the ESP32 and trigger
                      re-registration.
                    </div>
                  ) : (
                    moduleList.slice(0, 4).map((module) => (
                      <div
                        key={module.id}
                        className="rounded-xl border p-4"
                      >
                        <div className="mb-3 flex flex-wrap items-center gap-2">
                          <Badge variant="outline">{module.moduleType}</Badge>
                          <Badge variant={module.connected ? "default" : "secondary"}>
                            {module.connected ? "Connected" : "Disconnected"}
                          </Badge>
                        </div>


                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="modules" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Runtime Module Registry</CardTitle>
                <CardDescription>
                  Every registered module in your Zustand runtime map.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {moduleList.length === 0 ? (
                  <div className="rounded-lg border p-4 text-sm text-muted-foreground">
                    No modules in runtime store yet.
                  </div>
                ) : (
                  <div className="grid gap-4 lg:grid-cols-2">
                    {moduleList.map((module) => (
                      <Card key={module.id}>
                        <CardHeader className="pb-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline">{module.moduleType}</Badge>
                            <Badge
                              variant={module.connected ? "default" : "secondary"}
                            >
                              {module.connected ? "Connected" : "Disconnected"}
                            </Badge>
                          </div>
                          <CardTitle className="flex items-center gap-2 text-base">
                            <Cpu className="h-4 w-4" />
                            <span className="break-all">{module.id}</span>
                          </CardTitle>
                        </CardHeader>

                        <CardContent className="space-y-4">
                          <div>
                            <div className="mb-2 text-sm font-medium">Capabilities</div>
                            <pre className="overflow-auto rounded-md bg-muted/50 p-3 text-xs">
                              {JSON.stringify(module.payload, null, 2)}
                            </pre>
                          </div>

                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="serial" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Serial Inspector</CardTitle>
                <CardDescription>
                  Raw incoming serial data before and after runtime parsing.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="max-h-[520px] overflow-auto rounded-lg border bg-muted/40 p-4 text-xs leading-6">
                  {lastSerialMessage}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}

export default App
