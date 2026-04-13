import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      getSerialPorts: () => Promise<any[]>
      connectToPort: (path: string) => Promise<{success: boolean, error?: any}>
      sendCommand: (cmd: object) => void
      onSerialData: (callback: (data: string) => void) => void
      autoConnect: () => Promise<{ ok: boolean, path?: string, portInfo?: any, error?: any }>
    }
  }
}
