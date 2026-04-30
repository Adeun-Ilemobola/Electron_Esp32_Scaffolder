import * as React from "react"
import FindConnect from "./components/FindConnect"
import { useRuntimeStore } from "./zustand/RuntimeStore"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"

import {
  Activity,
  Boxes,
  Cpu,
  Info,
  PlugZap,
  RotateCcw,
  TerminalSquare,
  Wifi,
  WifiOff,
} from "lucide-react"

type IncomingPacket = {
  kind: string
  id: string
  moduleType: string
  payload: Record<string, any>
}

function App(): React.JSX.Element {
  const [connectedPath, setConnectedPath] = React.useState<string | null>(null)
  const [lastSerialMessage, setLastSerialMessage] = React.useState("No serial data yet.")
  const [logs, setLogs] = React.useState<Record<string, string>>({})
  const [lastPacket, setLastPacket] = React.useState<IncomingPacket | null>(null)

  const modules = useRuntimeStore((state) => state.modules)
  const registerModule = useRuntimeStore((state) => state.registerModule)
  const patchModuleState = useRuntimeStore((state) => state.patchModuleState)
  const removeModule = useRuntimeStore((state) => state.removeModule)

  const moduleList = React.useMemo(() => Object.values(modules), [modules])

  const totalModules = moduleList.length
  const connectedModules = moduleList.filter((module) => module.connected).length

  const groupedModules = React.useMemo(() => {
    return moduleList.reduce<Record<string, typeof moduleList>>((groups, module) => {
      const key = module.moduleType
      groups[key] ??= []
      groups[key].push(module)
      return groups
    }, {})
  }, [moduleList])

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

        if (kind === "register") {
          registerModule({
            id: data.id,
            moduleType: data.moduleType as any,
            connected: true,
            payload: data.payload ?? {},
          })
          return
        }

        if (kind === "state") {
          const existing = modules[data.id]

          if (!existing) {
            registerModule({
              id: data.id,
              moduleType: data.moduleType as any,
              connected: true,
              payload: data.payload ?? {},
            })
            return
          }

          patchModuleState(data.id, data.payload ?? {})
          return
        }

        if (kind === "remove" || kind === "disconnect") {
          removeModule(data.id)
          return
        }

        if (kind === "log") {
          const now = new Date().toISOString()
          const message = data.payload?.message ?? ""

          setLastSerialMessage(message)
          setLogs((prev) => ({
            ...prev,
            [now]: message,
          }))
        }
      } catch (err) {
        console.error("[RENDERER] parse failed:", err)
      }
    })
  }, [modules, patchModuleState, registerModule, removeModule])

  const sendReregister = (): void => {
    window.api.sendCommand({ cmd: "re-register" })
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-5 py-4">
        <header className="flex items-center justify-between gap-4 border-b pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl border bg-muted/40">
              <Cpu className="h-5 w-5" />
            </div>

            <div>
              <h1 className="text-base font-semibold tracking-tight">
                ESP32 Runtime
              </h1>
              <p className="text-xs text-muted-foreground">
                Clean module workspace
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant={connectedPath ? "default" : "secondary"} className="gap-1.5">
              {connectedPath ? (
                <Wifi className="h-3.5 w-3.5" />
              ) : (
                <WifiOff className="h-3.5 w-3.5" />
              )}
              {connectedPath ? "Connected" : "Disconnected"}
            </Badge>

            <Button variant="outline" size="sm" onClick={sendReregister}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Re-register
            </Button>

            <SystemDrawer
              connectedPath={connectedPath}
              totalModules={totalModules}
              connectedModules={connectedModules}
              lastPacket={lastPacket}
              lastSerialMessage={lastSerialMessage}
              logs={logs}
              onClearLogs={() => setLogs({})}
            />
          </div>
        </header>

        <section className="grid flex-1 gap-6 py-6 lg:grid-cols-[360px_1fr]">
          <aside className="space-y-4">
            <FindConnect
              connectedPath={connectedPath}
              setConnectedPath={setConnectedPath}
            />

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Boxes className="h-4 w-4" />
                  Runtime Summary
                </CardTitle>
                <CardDescription>
                  Small status view, not a full dashboard.
                </CardDescription>
              </CardHeader>

              <CardContent className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border bg-muted/30 p-3">
                  <div className="text-2xl font-semibold">{totalModules}</div>
                  <div className="text-xs text-muted-foreground">Modules</div>
                </div>

                <div className="rounded-xl border bg-muted/30 p-3">
                  <div className="text-2xl font-semibold">{connectedModules}</div>
                  <div className="text-xs text-muted-foreground">Online</div>
                </div>
              </CardContent>
            </Card>
          </aside>

          <section className="min-w-0 space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold tracking-tight">
                  Modules
                </h2>
                <p className="text-sm text-muted-foreground">
                  Registered ESP32 modules appear here as they come online.
                </p>
              </div>
            </div>

            {moduleList.length === 0 ? (
              <EmptyRuntimeState onReregister={sendReregister} />
            ) : (
              <div className="space-y-5">
                {Object.entries(groupedModules).map(([moduleType, modules]) => (
                  <section key={moduleType} className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{moduleType}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {modules.length} registered
                      </span>
                    </div>

                    <div className="grid gap-4 xl:grid-cols-2">
                      {modules.map((module) => (
                        <ModuleCard key={module.id} module={module} />
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            )}
          </section>
        </section>
      </div>
    </main>
  )
}

type ModuleCardProps = {
  module: {
    id: string
    moduleType: string
    connected: boolean
    payload: Record<string, any>
  }
}

function ModuleCard({ module }: ModuleCardProps): React.JSX.Element {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="space-y-3 pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Cpu className="h-4 w-4 shrink-0" />
              <span className="truncate">{module.moduleType}</span>
            </CardTitle>

            <CardDescription className="break-all font-mono text-xs">
              {module.id}
            </CardDescription>
          </div>

          <Badge variant={module.connected ? "default" : "secondary"}>
            {module.connected ? "Online" : "Offline"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="rounded-xl border bg-muted/30 p-3">
          <div className="mb-2 text-xs font-medium text-muted-foreground">
            Payload
          </div>

          <pre className="max-h-48 overflow-auto text-xs leading-5">
            {JSON.stringify(module.payload, null, 2)}
          </pre>
        </div>
      </CardContent>
    </Card>
  )
}

type EmptyRuntimeStateProps = {
  onReregister: () => void
}

function EmptyRuntimeState({ onReregister }: EmptyRuntimeStateProps): React.JSX.Element {
  return (
    <Card className="border-dashed">
      <CardContent className="flex min-h-[320px] flex-col items-center justify-center gap-4 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl border bg-muted/40">
          <PlugZap className="h-6 w-6 text-muted-foreground" />
        </div>

        <div className="max-w-sm space-y-1">
          <h3 className="font-medium">No modules registered yet</h3>
          <p className="text-sm text-muted-foreground">
            Connect your ESP32, then ask it to re-register its modules.
          </p>
        </div>

        <Button variant="outline" onClick={onReregister}>
          <RotateCcw className="mr-2 h-4 w-4" />
          Re-register Modules
        </Button>
      </CardContent>
    </Card>
  )
}

type SystemDrawerProps = {
  connectedPath: string | null
  totalModules: number
  connectedModules: number
  lastPacket: IncomingPacket | null
  lastSerialMessage: string
  logs: Record<string, string>
  onClearLogs: () => void
}

function SystemDrawer({
  connectedPath,
  totalModules,
  connectedModules,
  lastPacket,
  lastSerialMessage,
  logs,
  onClearLogs,
}: SystemDrawerProps): React.JSX.Element {
  return (
    <Drawer direction="right">
      <DrawerTrigger asChild>
        <Button variant="outline" size="sm">
          <Info className="mr-2 h-4 w-4" />
          System
        </Button>
      </DrawerTrigger>

      <DrawerContent className="ml-auto h-full w-full max-w-xl rounded-none border-l">
        <DrawerHeader>
          <DrawerTitle>System Information</DrawerTitle>
          <DrawerDescription>
            Connection, runtime, and serial details.
          </DrawerDescription>
        </DrawerHeader>

        <ScrollArea className="h-[calc(100vh-96px)] px-4 pb-6">
          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <PlugZap className="h-4 w-4" />
                  Connection
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-2">
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
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Activity className="h-4 w-4" />
                  Runtime
                </CardTitle>
              </CardHeader>

              <CardContent className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border bg-muted/30 p-3">
                  <div className="text-2xl font-semibold">{totalModules}</div>
                  <div className="text-xs text-muted-foreground">Total modules</div>
                </div>

                <div className="rounded-xl border bg-muted/30 p-3">
                  <div className="text-2xl font-semibold">{connectedModules}</div>
                  <div className="text-xs text-muted-foreground">Connected</div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Last Packet</CardTitle>
                <CardDescription>
                  Last parsed JSON packet from the ESP32.
                </CardDescription>
              </CardHeader>

              <CardContent>
                <pre className="max-h-52 overflow-auto rounded-xl border bg-muted/30 p-3 text-xs leading-5">
                  {lastPacket
                    ? JSON.stringify(lastPacket, null, 2)
                    : "No parsed packet yet."}
                </pre>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <TerminalSquare className="h-4 w-4" />
                  Last Raw Message
                </CardTitle>
              </CardHeader>

              <CardContent>
                <pre className="max-h-40 overflow-auto rounded-xl border bg-muted/30 p-3 text-xs leading-5">
                  {lastSerialMessage}
                </pre>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="relative pb-3">
                <CardTitle className="text-sm">Logs</CardTitle>
                <CardDescription>
                  Runtime log messages from incoming packets.
                </CardDescription>

                <Button
                  className="absolute right-6 top-4"
                  variant="outline"
                  size="sm"
                  onClick={onClearLogs}
                >
                  Clear
                </Button>
              </CardHeader>

              <CardContent>
                <div className="max-h-72 overflow-y-auto rounded-xl border bg-muted/30 p-3 text-xs leading-5">
                  {Object.keys(logs).length === 0 ? (
                    <p className="text-muted-foreground">No logs yet.</p>
                  ) : (
                    Object.entries(logs).map(([timestamp, message]) => (
                      <div key={timestamp} className="mb-2">
                        <span className="font-mono text-muted-foreground">
                          [{timestamp}]
                        </span>{" "}
                        <span className="font-mono">{message}</span>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </ScrollArea>
      </DrawerContent>
    </Drawer>
  )
}

export default App