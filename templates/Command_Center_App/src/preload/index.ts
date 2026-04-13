import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {
  getSerialPorts: () => ipcRenderer.invoke('get-serial-ports'),
  connectToPort: (path: string) => ipcRenderer.invoke('connect-port', path),
  sendCommand: (cmd: object) => ipcRenderer.send('send-command', cmd),
  onSerialData: (callback: (data: string) => void) => {
    // Listen for the ESP32's reply
    ipcRenderer.on('serial-data', (_event, value) => callback(value));
  },
  autoConnect: () => ipcRenderer.invoke('serial:autoConnect')
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}
