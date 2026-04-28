# Electron + ESP32 Scaffolder

A reusable project generator for building **desktop-controlled ESP32 systems**.

This project combines:

- a **Python CustomTkinter scaffolder**
- an **Electron + React + TypeScript command-center UI**
- an **ESP32 PlatformIO firmware template**
- a shared **serial JSON protocol**
- a runtime module registry for dynamic hardware discovery

The goal is simple: create new ESP32 + desktop-control projects without rebuilding the same Electron, serial, UI, firmware, and folder setup every time.

---

## Current Architecture

```txt
Python Scaffolder App
        │
        │ generates
        ▼
Project Root
├── ui_project-slug/
│   ├── Electron + React + TypeScript UI
│   ├── SerialPort main-process bridge
│   ├── Preload API
│   ├── Zustand runtime store
│   ├── Tailwind CSS + shadcn/ui
│   └── Runtime dashboard
│
├── esp_project-slug/
│   ├── PlatformIO ESP32 firmware project
│   ├── Arduino framework
│   ├── C++ hardware modules
│   └── serial JSON packet output
│
└── .scaffold/
    └── project.json
```

The generated Electron app controls and monitors the ESP32 over serial communication. The ESP32 announces hardware modules, sends state updates, and receives commands from the desktop UI.

---

## What the Scaffolder Does

The Python scaffolder is the main entry point.

It provides a desktop UI where you choose:

- project name
- destination folder

When you click **Generate**, the scaffolder:

1. validates the destination folder
2. slugifies the project name
3. creates a unique project ID
4. creates a project root folder
5. runs the Electron scaffold generator
6. applies your custom UI template overlay
7. patches generated Electron config files
8. installs Electron/UI dependencies with Bun
9. generates shadcn/ui components
10. creates the ESP32 PlatformIO folder from your ESP template
11. writes scaffold metadata
12. adds the project to the recent-projects list

The scaffolder is not just copying a finished project anymore. It now creates a real Electron base first, then layers your architecture on top.

---

## Generated Folder Structure

Example for a project named `Servo Controller`:

```txt
servo-controller/
├── ui_servo-controller/
│   ├── src/
│   │   ├── main/
│   │   ├── preload/
│   │   └── renderer/
│   │       └── src/
│   │           ├── assets/
│   │           ├── components/
│   │           ├── lib/
│   │           ├── zustand/
│   │           ├── App.tsx
│   │           └── main.tsx
│   ├── components.json
│   ├── electron.vite.config.ts
│   ├── electron-builder.yml
│   ├── package.json
│   └── bun.lock
│
├── esp_servo-controller/
│   ├── platformio.ini
│   ├── src/
│   ├── include/
│   ├── lib/
│   └── test/
│
└── .scaffold/
    └── project.json
```

The generated metadata file stores the relationship between both sides:

```json
{
  "name": "Servo Controller",
  "project_id": "esp-servo-controller-a1b2c3",
  "project_slug": "servo-controller",
  "project_root": ".../servo-controller",
  "ui_path": ".../servo-controller/ui_servo-controller",
  "esp32_path": ".../servo-controller/esp_servo-controller",
  "type": "ui_and_esp32",
  "created_at": "2026-04-27T17:30:00"
}
```

---

## Template Layout

The current scaffolder expects the new template layout:

```txt
templatesV2/
├── ui/
│   ├── src/
│   │   ├── main/
│   │   ├── preload/
│   │   └── renderer/
│   │       └── src/
│   │           ├── assets/
│   │           ├── components/
│   │           ├── lib/
│   │           ├── zustand/
│   │           ├── App.tsx
│   │           └── main.tsx
│   ├── components.json
│   ├── tsconfig.json
│   └── tsconfig.web.json
│
└── esp/
    ├── platformio.ini
    ├── src/
    ├── include/
    ├── lib/
    └── test/
```

The UI template is used as an **overlay**. It does not blindly replace the whole Electron project.

---

## Template Overlay System

The newer scaffolder uses a safer overlay system.

Instead of deleting and replacing everything, it applies template files like this:

| Situation | Behavior |
| --- | --- |
| File does not exist | Create it |
| File already exists and is identical | Skip it |
| File already exists and changed | Update it |
| File is protected | Do not overwrite it |
| Junk folder/file | Ignore it |

Ignored paths include:

```txt
node_modules
dist
out
build
.git
.pio
__pycache__
.DS_Store
```

Important generated Electron files are protected from blind overwrite:

```txt
package.json
bun.lock
electron.vite.config.ts
electron-builder.yml
dev-app-update.yml
```

Those files are patched intentionally instead of copied over blindly.

---

## Electron Base Generation

The UI project is created using:

```bash
bunx @quick-start/create-electron@latest ui_project-slug --template react-ts
```

Because this generator asks interactive questions, the Python engine uses `pexpect` to answer the prompts automatically.

Current prompt choices:

```txt
Add Electron updater plugin: Yes
Enable Electron download mirror proxy: No
```

After generation, the scaffolder patches the project for your architecture.

---

## Electron Config Patches

The scaffolder patches `electron.vite.config.ts` so the generated app understands:

- the `@` alias
- Tailwind CSS v4 through the Vite plugin

The renderer config needs the important pieces below:

```ts
import { resolve } from "path"
import tailwindcss from "@tailwindcss/vite"

renderer: {
  resolve: {
    alias: {
      "@": resolve("src/renderer/src"),
    },
  },
  plugins: [
    react(),
    tailwindcss(),
  ],
}
```

This is required because TypeScript and Vite are separate systems.

`tsconfig.web.json` helps the editor understand `@/...`.

`electron.vite.config.ts` helps the actual Vite dev server understand `@/...`.

---

## UI Stack

The generated Electron command center uses:

- Electron
- electron-vite
- React
- TypeScript
- Bun
- Vite
- Tailwind CSS
- shadcn/ui
- Radix UI
- Lucide React
- Zustand
- Zod
- SerialPort
- Electron Builder

The Electron app is split into:

```txt
src/main/       Electron main process
src/preload/    Safe bridge between main and renderer
src/renderer/   React UI
```

---

## shadcn/ui Components

The scaffolder generates the required shadcn/ui components automatically.

Current component set:

```txt
button
card
input
label
dialog
slider
select
switch
sonner
badge
separator
tabs
```

These components are generated into:

```txt
src/renderer/src/components/ui/
```

Example import:

```ts
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
```

---

## Tailwind CSS

The renderer CSS entry file should be imported from `main.tsx`:

```ts
import "./assets/main.css"
```

For Tailwind CSS v4, the main CSS file should include:

```css
@import "tailwindcss";
@import "tw-animate-css";
```

If the app renders with plain browser styling, check:

1. `main.tsx` imports the CSS file
2. `main.css` imports Tailwind
3. `electron.vite.config.ts` uses `tailwindcss()`
4. `tailwindcss` and `@tailwindcss/vite` are installed

---

## Runtime Dashboard

The React dashboard is runtime-driven.

It displays information coming from the serial bridge and the Zustand runtime store:

- connection status
- connected serial path
- registered module count
- connected module count
- last packet kind
- last raw serial message
- module registry
- serial inspector
- re-register command
- test command buttons

The UI is designed so the ESP32 can announce what exists instead of the React app hardcoding every hardware component.

---

## Runtime Store

The renderer uses Zustand as a dynamic module registry.

A module entry follows this shape:

```ts
type ModuleEntry = {
  id: string
  moduleType: string
  connected: boolean
  payload: Record<string, any>
}
```

The store exposes actions like:

```ts
registerModule(module)
patchModuleState(id, patch)
removeModule(id)
```

This allows the UI to update based on packets coming from the ESP32.

---

## Serial Communication

Communication between Electron and the ESP32 uses newline-separated JSON packets.

The main process handles the actual SerialPort connection.

The renderer communicates through the preload API.

```txt
Renderer React UI
      │
      ▼
Preload API
      │
      ▼
Electron Main Process
      │
      ▼
SerialPort
      │
      ▼
ESP32
```

The renderer should not directly access Node APIs. The preload layer exposes only the safe commands/events the UI needs.

---

## Packet Contract

Incoming ESP32 packets follow this general shape:

```ts
type IncomingPacket = {
  kind: string
  id: string
  moduleType: string
  payload: Record<string, any>
}
```

Example register packet:

```json
{
  "kind": "register",
  "id": "led_12",
  "moduleType": "led",
  "payload": {
    "state": false
  }
}
```

Example state packet:

```json
{
  "kind": "state",
  "id": "button_18",
  "moduleType": "button",
  "payload": {
    "isPressed": true
  }
}
```

Example log packet:

```json
{
  "kind": "log",
  "id": "system",
  "moduleType": "system",
  "payload": {
    "message": "All modules registered"
  }
}
```

---

## Packet Kinds

| Kind | Direction | Purpose |
| --- | --- | --- |
| `register` | ESP32 → Electron | Announces that a module exists |
| `state` | ESP32 → Electron | Sends state changes |
| `remove` | ESP32 → Electron | Removes a module from the UI registry |
| `disconnect` | ESP32 → Electron | Marks a module/device as disconnected |
| `log` | ESP32 → Electron | Sends firmware-side logs |
| `command` | Electron → ESP32 | Sends commands to the firmware |

---

## Command Flow

The UI can send commands to the ESP32 through the preload API.

Example:

```ts
window.api.sendCommand({ cmd: "re-register" })
window.api.sendCommand({ cmd: "toggle_led" id:"64hgfdg7fg" })
```

The firmware reads serial input, parses JSON, and decides what action to perform.

Example command packet:

```json
{
  "cmd": "re-register"
}
```

The ESP32 can respond by sending fresh `register` packets for all known modules.

---

## ESP32 Firmware Template

The ESP32 side is a PlatformIO project using the Arduino framework.

The scaffolder currently creates the ESP32 side by copying the known-good template from:

```txt
templatesV2/esp
```

This avoids requiring the `pio` CLI to be available globally from the Python app.

Expected ESP32 output:

```txt
esp_project-slug/
├── platformio.ini
├── src/
├── include/
├── lib/
└── test/
```

The ESP32 template can still be opened and managed with PlatformIO inside VS Code.

---

## Firmware Architecture

The firmware uses a module-style C++ structure.

A hardware module should own:

- module ID
- module type
- pin configuration
- local state
- setup behavior
- update/read behavior
- command behavior
- JSON serialization behavior

Examples:

- LED module
- Button module
- Servo module
- Sensor module
- Motor module
- Relay module

The long-term direction is for each module to be self-describing, so the Electron UI can build its runtime dashboard from the ESP32’s announcements.

---

## Example Module Registration Flow

```txt
ESP32 starts
    │
    ▼
Modules are created
    │
    ▼
Each module sends a register packet
    │
    ▼
Electron receives serial JSON
    │
    ▼
Renderer parses the packet
    │
    ▼
Zustand registerModule() stores it
    │
    ▼
React dashboard updates
```

---

## Example State Update Flow

```txt
Hardware state changes
    │
    ▼
Module updates local state
    │
    ▼
Module sends state packet
    │
    ▼
Electron receives packet
    │
    ▼
Renderer calls patchModuleState()
    │
    ▼
Dashboard refreshes
```

---

## Development Workflow

Generate a project:

1. Open the Python scaffolder.
2. Enter a project name.
3. Select a destination folder.
4. Click **Generate**.
5. Open the generated project in VS Code.

Run the Electron app:

```bash
cd ui_project-slug
bun run dev
```

Open the ESP32 firmware:

```txt
esp_project-slug/
```

Then use PlatformIO to:

- build
- upload
- monitor serial output

---

## Scaffolder Logging

The Python app uses structured log events.

Log levels:

```txt
INFO
SUCCESS
WARNING
ERROR
STEP
COMMAND
```

The engine sends log events back to the UI using a callback:

```txt
ScaffoldEngineV1
      │
      ▼
LogEvent callback
      │
      ▼
CustomTkinter log textbox
```

This makes long scaffolding operations easier to understand because the UI can show:

- what step is running
- what command is executing
- command output
- warnings
- errors
- success messages

---

## Recent Projects

The scaffolder stores recent projects locally:

```txt
~/.electron_esp32_scaffolder/recent_projects.json
```

Recent projects are shown as cards in the UI.

Clicking a card opens the project path in VS Code.

---

## Important Requirements

The scaffolder assumes these tools are available:

```txt
Python 3
Bun
Node-compatible package ecosystem
VS Code
PlatformIO extension for ESP32 development
```

Python dependency:

```bash
python3 -m pip install pexpect
```

The ESP32 template no longer requires the `pio` CLI during project generation, but PlatformIO is still needed for building and uploading firmware.

---

## Current Features

- Python CustomTkinter desktop scaffolder
- Structured engine logging with callbacks
- Recent project tracking
- VS Code launch from project cards
- Electron project generation through `@quick-start/create-electron`
- Automated interactive Electron prompt handling with `pexpect`
- Safe template overlay system
- Protected generated config files
- Automatic Electron config patching
- Automatic Tailwind/Vite alias patching
- Bun dependency installation
- shadcn/ui component generation
- ESP32 PlatformIO template generation
- `.scaffold/project.json` metadata
- Electron main/preload/renderer architecture
- SerialPort scanning and connection logic
- Runtime module registry with Zustand
- JSON packet parsing
- Runtime dashboard foundation
- Firmware template foundation

---

## Design Principles

### Generate the boring structure

The scaffolder handles repeated project setup so new builds start faster.

### Use overlays instead of blind copies

Generated projects should be updated carefully. The scaffolder adds and updates architecture files without carelessly overwriting important generated config.

### Keep UI and firmware together

Each generated project contains both the Electron command center and the ESP32 firmware project.

### Make hardware modules self-describing

The ESP32 should tell the UI what modules exist, instead of the UI hardcoding everything.

### Use JSON as the serial contract

JSON packets make communication easier to inspect, log, debug, and extend.

### Keep React state runtime-driven

The frontend stores connected modules dynamically in Zustand.

### Patch generated config intentionally

Important files like `package.json`, `electron.vite.config.ts`, and `electron-builder.yml` should be patched directly, not blindly replaced.

---

## Known Notes

### `tsconfig.web.json` baseUrl warning

TypeScript may warn that `baseUrl` is deprecated.

That warning is not usually what breaks the app. The important runtime alias must exist in:

```txt
electron.vite.config.ts
```

### Plain HTML with no styling

If the app runs but looks unstyled, check:

```txt
src/renderer/src/main.tsx
src/renderer/src/assets/main.css
electron.vite.config.ts
package.json dependencies
```

The usual cause is that Tailwind is installed but not wired into the Vite renderer config.

### Import errors for `@/components/ui/...`

If Vite cannot resolve `@/components/ui/button`, the file might exist but Vite may not know the `@` alias.

Check:

```txt
electron.vite.config.ts
```

The renderer config must include:

```ts
resolve: {
  alias: {
    "@": resolve("src/renderer/src"),
  },
}
```

---

## Future Improvements

Possible next improvements:

- Generate a README inside every scaffolded project
- Add board selection for ESP32 variants
- Add PlatformIO environment selection
- Add firmware-side base module class
- Add firmware-side module registry
- Add Zod validation for incoming packets
- Add Zod validation for outgoing commands
- Add heartbeat and timeout packets
- Add reconnect logic
- Add module capability descriptions
- Add support for multiple sensors and outputs
- Add project preset selection
- Add cleanup/rollback when generation fails
- Add post-generation validation checks
- Add prettier/formatter pass after generation
- Add visual architecture diagram inside the app
- Add a proper module marketplace/template library later

---

## End-to-End Flow

```txt
1. Python scaffolder creates a new project.
2. Electron base project is generated.
3. UI template overlay is applied.
4. Electron config is patched.
5. Bun installs dependencies.
6. shadcn/ui components are generated.
7. ESP32 template is copied.
8. Metadata is written.
9. User opens the project in VS Code.
10. Electron app starts.
11. Main process scans serial ports.
12. ESP32 sends JSON packets.
13. Renderer updates Zustand runtime store.
14. React dashboard displays the live device state.
15. User sends commands back to the ESP32.
```

---

## Summary

This project is a reusable foundation for building ESP32 systems controlled by an Electron desktop app.

The Python scaffolder solves project setup. The Electron command center solves desktop control and serial communication. The ESP32 template solves the firmware starting point. The JSON protocol connects both sides.

Together, they create a repeatable workflow for building hardware projects without starting from zero every time.
