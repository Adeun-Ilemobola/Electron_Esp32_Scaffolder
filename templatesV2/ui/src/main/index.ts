import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { SerialPort } from 'serialport'
import { ReadlineParser } from '@serialport/parser-readline'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

let mainWindow: BrowserWindow | null = null
let activePort: SerialPort | null = null
let activeParser: ReadlineParser | null = null

function SmartLog(...args: unknown[]): void {
  console.log('[MAIN]', ...args)
}

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

async function closeActivePort(): Promise<void> {
  if (!activePort) return

  const portToClose = activePort
  const parserToClear = activeParser

  activePort = null
  activeParser = null

  parserToClear?.removeAllListeners()
  portToClose.removeAllListeners()

  if (!portToClose.isOpen) return

  await new Promise<void>((resolve) => {
    portToClose.close(() => resolve())
  })

  SmartLog('Previous port closed.')
}

function attachSerialListeners(port: SerialPort): void {
  const parser = port.pipe(new ReadlineParser({ delimiter: '\n' }))
  activeParser = parser

  parser.on('data', (data: string) => {
    SmartLog('DATA:', data)
    mainWindow?.webContents.send('serial-data', data)
  })

  port.on('error', (err) => {
    SmartLog('PORT ERROR:', err)
  })

  port.on('close', () => {
    SmartLog('Port closed.')
  })
}

async function openSerialPort(path: string) {
  await closeActivePort()

  const port = new SerialPort({
    path,
    baudRate: 115200,
    autoOpen: false
  })

  await new Promise<void>((resolve, reject) => {
    port.open((err) => {
      if (err) reject(err)
      else resolve()
    })
  })

  activePort = port
  attachSerialListeners(port)

  SmartLog('Connected successfully to:', path)

  return { success: true, path }
}

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  ipcMain.handle('connect-port', async (_event, path: string) => {
    try {
      return await openSerialPort(path)
    } catch (error) {
      SmartLog('Connection failed:', error)
      return { success: false, error: String(error) }
    }
  })

  ipcMain.handle('serial:autoConnect', async () => {
    try {
      const ports = await SerialPort.list()

      SmartLog('Scanning ports...')
      ports.forEach((p, i) => {
        SmartLog(`Port ${i + 1}:`, JSON.stringify(p, null, 2))
      })

      const match = ports.find((p) => {
        const vendorId = (p.vendorId ?? '').toLowerCase()
        const manufacturer = (p.manufacturer ?? '').toLowerCase()
        const pathName = (p.path ?? '').toLowerCase()

        return (
          vendorId === '303a' ||
          vendorId === '10c4' ||
          vendorId === '1a86' ||
          manufacturer.includes('silicon labs') ||
          manufacturer.includes('wch') ||
          pathName.includes('usb') ||
          pathName.startsWith('com')
        )
      })

      if (!match) {
        SmartLog('No matching port found.')
        return { ok: false, error: 'No matching port found' }
      }

      await openSerialPort(match.path)

      return {
        ok: true,
        path: match.path,
        portInfo: match
      }
    } catch (error) {
      SmartLog('autoConnect failed:', error)
      return {
        ok: false,
        error: String(error)
      }
    }
  })

  ipcMain.on('send-command', (_, command: object) => {
    if (activePort && activePort.isOpen) {
      const payload = JSON.stringify(command) + '\n'
      SmartLog('SEND:', payload)
      activePort.write(payload)
    } else {
      SmartLog('SEND FAILED: no active open port')
    }
  })

  ipcMain.on('ping', () => console.log('pong'))

  ipcMain.handle('get-serial-ports', async () => {
    try {
      const ports = await SerialPort.list()
      SmartLog('Available serial ports:', ports)
      return ports
    } catch (error) {
      SmartLog('Failed to list ports:', error)
      return []
    }
  })

  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
