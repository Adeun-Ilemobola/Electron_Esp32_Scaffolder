import * as React from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

type SerialPortInfo = {
  path: string
  manufacturer?: string
  serialNumber?: string
}

type FindConnectProps = {
  connectedPath: string | null
  setConnectedPath: React.Dispatch<React.SetStateAction<string | null>>
}

export default function FindConnect({
  connectedPath,
  setConnectedPath,
}: FindConnectProps): React.JSX.Element {
  const [ports, setPorts] = React.useState<SerialPortInfo[]>([])
  const [isScanning, setIsScanning] = React.useState(false)

  const scanPorts = async (): Promise<void> => {
    setIsScanning(true)

    try {
      const availablePorts = await window.api.getSerialPorts()

      setPorts(availablePorts ?? [])
      const nowconnected = await window.api.autoConnect()
      if (nowconnected.ok && nowconnected.path) {
        setConnectedPath(nowconnected.path)
      }
    } catch (error) {
      console.error("Failed to scan serial ports:", error)
      setPorts([])
    } finally {
      setIsScanning(false)
    }
  }

  const connectToDevice = async (path: string): Promise<void> => {
    try {
      const result = await window.api.connectToPort(path)

      if (result.success) {
        setConnectedPath(path)
      }
    } catch (error) {
      console.error("Failed to connect to device:", error)
    }
  }

  React.useEffect(() => {
    void scanPorts()
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Find and Connect</CardTitle>
        <CardDescription>
          Scan available serial ports and connect to your ESP32.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => void scanPorts()} disabled={isScanning}>
            {isScanning ? "Scanning..." : "Scan USB Ports"}
          </Button>

          <Badge variant={connectedPath ? "default" : "secondary"}>
            {connectedPath ? `Connected: ${connectedPath}` : "No device connected"}
          </Badge>
        </div>

        <div className="space-y-3">
          {ports.length === 0 ? (
            <div className="rounded-md border p-4 text-sm text-muted-foreground">
              No ports found yet. Try scanning again.
            </div>
          ) : (
            ports.map((port) => {
              const isConnected = connectedPath === port.path

              return (
                <div
                  key={port.path}
                  className="flex flex-col gap-3 rounded-lg border p-4 md:flex-row md:items-center md:justify-between"
                >
                  <div className="space-y-1">
                    <div className="font-medium">{port.path}</div>
                    <div className="text-sm text-muted-foreground">
                      {port.manufacturer || "Unknown manufacturer"}
                    </div>
                  </div>

                  <Button
                    onClick={() => void connectToDevice(port.path)}
                    disabled={isConnected}
                    variant={isConnected ? "secondary" : "default"}
                  >
                    {isConnected ? "Connected" : "Connect"}
                  </Button>
                </div>
              )
            })
          )}
        </div>
      </CardContent>
    </Card>
  )
}
