# Electron + ESP32 PlatformIO Architecture

A reusable scaffolding and runtime architecture for building desktop-controlled ESP32 projects.

This system combines a **Python scaffolder**, an **Electron + React command-center UI**, and an **ESP32 PlatformIO firmware template** into one repeatable project setup. The goal is to make it fast to create new hardware/software projects where a desktop app can discover, monitor, and control ESP32 modules over serial communication.

---

## What This System Does

This architecture generates paired projects:

* an Electron desktop app for the user interface,
* an ESP32 PlatformIO firmware project for the hardware side,
* shared runtime behavior based on structured serial JSON messages,
* a module registration system so the UI can discover hardware modules dynamically.

Instead of rebuilding the same Electron, React, serial, ESP32, and module-state setup every time, the scaffolder creates a ready-to-use project from templates.

---

## High-Level Architecture

```txt
┌────────────────────────────┐
│ Python Scaffolder App       │
│ CustomTkinter Desktop Tool  │
└─────────────┬──────────────┘
              │
              │ Generates paired project
              ▼
┌────────────────────────────────────────────┐
│ Generated Project Root                      │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ Electron Command Center UI           │  │
│  │ React + TypeScript + Zustand         │  │
│  └─────────────────┬────────────────────┘  │
│                    │ Serial JSON            │
│                    ▼                        │
│  ┌──────────────────────────────────────┐  │
│  │ ESP32 PlatformIO Firmware            │  │
│  │ C++ Hardware Modules                 │  │
│  └──────────────────────────────────────┘  │
│                                            │
└────────────────────────────────────────────┘
```

---

## Core Idea

The ESP32 firmware exposes hardware features as **modules**.

Examples:

* LED module
* Button module
* Sensor module
* Motor module
* Relay module

Each module has:

* an ID,
* a module type,
* local state,
* setup logic,
* command behavior,
* JSON serialization behavior.

The Electron app does not need to know every module ahead of time. The ESP32 can announce modules over serial, and the Electron UI registers them dynamically in a runtime store.

---

## Project Generator

The Python scaffolder is the entry point for creating new projects.

It provides a small desktop UI where the user selects:

* project name,
* destination folder.

When the user clicks **Generate**, the scaffolder:

1. validates the selected destination folder,
2. slugifies the project name,
3. generates a unique project ID,
4. creates a project root folder,
5. copies the Electron UI template,
6. copies the ESP32 PlatformIO template,
7. patches `package.json`,
8. patches `electron-builder.yml`,
9. removes junk template folders,
10. writes scaffold metadata,
11. runs `bun install` in the Electron UI folder,
12. adds the generated project to the recent-projects list.

---

## Generated Folder Structure

A generated project follows this structure:

```txt
project-slug/
├── UI_Project Name/
│   ├── package.json
│   ├── electron-builder.yml
│   ├── src/
│   └── ...
│
├── esp_Project Name/
│   ├── platformio.ini
│   ├── src/
│   ├── include/
│   └── ...
│
└── .scaffold/
    └── project.json
```

The `.scaffold/project.json` file stores project metadata:

```json
{
  "name": "Project Name",
  "project_id": "esp-project-name-a1b2c3",
  "project_slug": "project-name",
  "project_root": ".../project-name",
  "ui_path": ".../project-name/UI_Project Name",
  "esp32_path": ".../project-name/esp_Project Name",
  "type": "ui_and_esp32"
}
```

---

## Template Layout

The scaffolder expects templates to exist in this structure:

```txt
templates/
├── Command_Center_App/
└── esp32/
```

`Command_Center_App` is the Electron desktop template.

`esp32` is the PlatformIO firmware template.

The generator copies both into the new project root so each generated project contains both its UI and firmware side.

---

## Scaffolder State

The scaffolder stores recent projects locally in the user home directory:

```txt
~/.electron_esp32_scaffolder/recent_projects.json
```

This allows the app to show recently generated projects as clickable cards. Clicking a recent project opens it in VS Code.

---

## Electron Command Center

The generated Electron app is the desktop control surface for the ESP32.

It is built with:

* Electron
* electron-vite
* React
* TypeScript
* Vite
* Zustand
* Zod
* SerialPort
* Tailwind CSS
* shadcn/ui
* Radix UI
* Lucide React
* Electron Builder

The app handles:

* auto-connection to the ESP32,
* serial message listening,
* JSON packet parsing,
* runtime module registration,
* module state updates,
* raw serial inspection,
* commands sent back to the ESP32.

---

## Electron Scripts

Common scripts:

```bash
npm run dev
npm run build
npm run start
npm run build:win
npm run build:mac
npm run build:linux
```

Development usually starts with:

```bash
npm run dev
```

---

## Runtime Store

The Electron renderer uses a Zustand store as the runtime registry for connected ESP32 modules.

Each module is represented as:

```ts
type ModuleEntry = {
  id: string
  moduleType: string
  connected: boolean
  payload: Record<string, any>
}
```

The runtime store exposes:

```ts
registerModule(module)
patchModuleState(id, patch)
removeModule(id)
```

This makes the frontend dynamic. Instead of hardcoding every module into React state, modules can register themselves from the firmware side.

---

## Serial Packet Contract

The firmware and Electron app communicate using newline-separated JSON packets.

The common packet shape is:

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

Example button state packet:

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
  "id": "101",
  "moduleType": "101",
  "payload": {
    "message": "All items are registered"
  }
}
```

---

## Packet Kinds

| Kind         | Direction        | Purpose                                     |
| ------------ | ---------------- | ------------------------------------------- |
| `register`   | ESP32 → Electron | Announces that a module exists.             |
| `state`      | ESP32 → Electron | Sends a state update for a module.          |
| `remove`     | ESP32 → Electron | Removes a module from the runtime registry. |
| `disconnect` | ESP32 → Electron | Marks or removes a disconnected module.     |
| `log`        | ESP32 → Electron | Sends firmware-side log messages to the UI. |
| `command`    | Electron → ESP32 | Sends a command to the firmware.            |

---

## Command Flow

The Electron app sends commands to the ESP32 using the preload API.

Example commands:

```ts
window.api.sendCommand({ cmd: "re-register" })
window.api.sendCommand({ cmd: "toggle_led" })
```

The ESP32 listens for incoming serial JSON, parses it, and responds based on the command.

For example, when the ESP32 receives:

```json
{
  "cmd": "re-register"
}
```

it can ask its modules to send fresh `register` packets back to the Electron app.

---

## Firmware Architecture

The ESP32 firmware is written in C++ and follows a module-based style.

The main firmware file is responsible for:

* starting serial communication,
* creating module instances,
* running the main loop,
* checking input modules,
* updating output modules,
* reading incoming serial commands,
* parsing JSON commands,
* calling module serialization functions.

Example runtime behavior:

```txt
Button is pressed
      │
      ▼
ESP32 reads button state
      │
      ▼
LED state toggles
      │
      ▼
LED sends state packet
      │
      ▼
Electron receives JSON
      │
      ▼
Zustand runtime store updates
      │
      ▼
React dashboard refreshes
```

---

## Firmware Modules

Hardware features are wrapped in C++ classes.

Current module examples:

* `Led`
* `Btu`

The naming can evolve over time. For readability, `Btu` may eventually become `Button` or `ButtonModule`, but the current idea is already clear: each hardware component owns its own behavior and serial representation.

---

## LED Module

The LED module owns:

* output pin,
* current state,
* module ID,
* setup behavior,
* `on()` behavior,
* `off()` behavior,
* `toggle()` behavior,
* `setState()` behavior,
* JSON serialization behavior.

Example LED module packet:

```json
{
  "kind": "state",
  "id": "led_12",
  "moduleType": "led",
  "payload": {
    "state": true
  }
}
```

The LED module can announce itself with `register` and publish state changes with `state`.

---

## Button Module

The button module owns:

* input pin,
* pull-up configuration,
* current pressed state,
* module ID,
* setup behavior,
* state reading behavior,
* JSON serialization behavior.

Example button module packet:

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

The button module supports both pull-up and non-pull-up input modes.

---

## Module Registration Flow

When a module is created, it can send a `register` packet.

```txt
ESP32 starts
    │
    ▼
Module setup runs
    │
    ▼
Module serializes itself as register packet
    │
    ▼
Electron receives packet
    │
    ▼
Renderer parses packet
    │
    ▼
Zustand registerModule() stores it
    │
    ▼
Dashboard displays module
```

This keeps the UI flexible because the ESP32 tells the UI what exists.

---

## State Update Flow

When a module changes, it sends a `state` packet.

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
Dashboard updates module payload
```

This is the core live-update mechanism.

---

## Re-Register Flow

The UI can request all modules to announce themselves again.

```txt
User clicks Re-register Modules
    │
    ▼
Electron sends command
    │
    ▼
ESP32 receives re-register
    │
    ▼
ESP32 asks modules to serialize register packets
    │
    ▼
Electron rebuilds runtime registry
```

This is useful after reconnecting, refreshing, or debugging serial communication.

---

## React Dashboard

The current dashboard includes:

* connection status,
* connected serial path,
* registered module count,
* connected module count,
* last packet kind,
* last raw serial message,
* runtime module registry,
* serial inspector,
* re-register button,
* LED toggle button.

The dashboard is intentionally runtime-driven. It reads from the Zustand module registry and displays whatever modules the ESP32 announces.

---

## Development Workflow

Typical workflow:

1. Open the Python scaffolder.
2. Enter a project name.
3. Select a destination folder.
4. Generate the project.
5. Open the generated project in VS Code.
6. Start the Electron app.

```bash
cd "UI_Project Name"
npm run dev
```

7. Open the ESP32 folder in PlatformIO.
8. Build and upload the firmware.
9. Connect the ESP32 over USB.
10. Use the Electron dashboard to inspect and control the device.

---

## Design Principles

### 1. Generate the boring structure

The scaffolder handles repeated setup work so new projects start faster.

### 2. Keep UI and firmware together

Each generated project contains both sides of the system.

### 3. Make modules self-describing

ESP32 modules announce their own ID, type, and state.

### 4. Use JSON as the serial contract

Structured JSON makes the communication easier to debug and extend.

### 5. Keep React state dynamic

The frontend uses a runtime registry instead of hardcoded component state.

### 6. Make debugging visible

Raw serial logs and runtime module views make hardware/software communication problems easier to inspect.

---

## Current Features

* Python desktop scaffolder
* Electron UI template generation
* ESP32 PlatformIO template generation
* Project metadata generation
* Recent project tracking
* VS Code launch from recent-project cards
* Automatic `bun install`
* Electron + React dashboard
* Serial communication layer
* JSON packet parsing
* Zustand runtime module registry
* Module registration packets
* Module state packets
* Firmware log packets
* Button input module
* LED output module
* Re-register command
* LED toggle command example

---

## Future Improvements

Possible improvements:

* Rename `Btu` to `Button` or `ButtonModule` for clarity.
* Add a shared protocol document.
* Add Zod schemas for incoming serial packets.
* Add command schemas for outgoing commands.
* Add heartbeat packets.
* Add reconnect and timeout handling.
* Add module capability descriptions.
* Add firmware-side base module class.
* Add module registry on the ESP32 side.
* Add support for multiple buttons, LEDs, sensors, and relays.
* Add generated README files inside every scaffolded project.
* Add board selection for different ESP32 variants.
* Add PlatformIO environment selection.
* Add a visual architecture diagram.
* Add automated checks after project generation.

---

## Example End-to-End Flow

```txt
1. Python scaffolder creates a new project.
2. User opens generated project in VS Code.
3. Electron app starts and auto-connects to ESP32.
4. Electron sends re-register command.
5. ESP32 modules send register packets.
6. React parses packets from serial.
7. Zustand stores modules by ID.
8. Dashboard displays modules.
9. User presses a physical button.
10. ESP32 toggles LED state.
11. LED module sends state packet.
12. Electron updates the runtime dashboard.
```

---

## Summary

This architecture is a reusable foundation for ESP32 projects controlled by an Electron desktop application.

The scaffolder solves project setup. The firmware module system solves hardware organization. The serial JSON protocol solves communication. The Zustand runtime registry solves dynamic UI state.

Together, they form a practical system for building desktop-controlled embedded projects without starting from scratch every time.
