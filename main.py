import customtkinter as ctk
from tkinter import filedialog
import subprocess
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re
import shutil
import threading
import uuid
from typing import Callable
from enum import Enum
import pexpect


# =========================================================
# PATHS / CONSTANTS
# =========================================================

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"



# Set up the overall theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

UI_TEMPLATE_FILES_DIR  = APP_DIR/"templatesV2"/"ui"
ESP32_TEMPLATE_FILES_DIR = APP_DIR/"templatesV2"/"esp"
dependencies_Installation_Commands_UI = [
    "shadcn", "class-variance-authority", "clsx", "tailwind-merge", "lucide-react", "tw-animate-css" ,"zod" ,"zustand"
   
]


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class ProjectSpec:
    name: str
    destination_root: str
    project_id: str
    project_slug: str


@dataclass
class ProjectRecord:
    name: str
    project_id: str
    path: str
# =========================================================
# HELPERS V1
# =========================================================
def stripAnsiCodes(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)

def run_cmd(cmd: list[str], cwd: Path, input_text: str | None = None):
    print("Running:", " ".join(cmd))

    subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        text=True,
        check=True,
    )


def copy_template_folder(source: Path, destination: Path):
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".DS_Store",
            "__pycache__",
            "node_modules",
            "dist",
            "out",
        ),
    )


class LogLevel(Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    STEP = "STEP"
    COMMAND = "COMMAND"


@dataclass(frozen=True)
class LogEvent:
    message: str
    level: LogLevel = LogLevel.INFO
    source: str = "APP"


LogCallback = Callable[[LogEvent], None]

def formatLogEvent(event: LogEvent) -> str:
    timestamp = datetime.now().strftime("%H:%M:%S")

    iconByLevel = {
        LogLevel.INFO: "ℹ️",
        LogLevel.SUCCESS: "✅",
        LogLevel.WARNING: "⚠️",
        LogLevel.ERROR: "❌",
        LogLevel.STEP: "🔧",
        LogLevel.COMMAND: "⌨️",
    }

    icon = iconByLevel.get(event.level, "•")
    return f"[{timestamp}] {icon} {event.level.value:<7} [{event.source}] {event.message}\n"

# =========================================================
# HELPERS
# =========================================================




def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def make_project_id(slug: str) -> str:
    short = uuid.uuid4().hex[:6]
    return f"esp-{slug}-{short}"


def load_recent_projects() -> list[ProjectRecord]:
    APP_STATE_DIR.mkdir(parents=True, exist_ok=True)

    if not RECENTS_FILE.exists():
        return []

    try:
        with open(RECENTS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [ProjectRecord(**item) for item in raw]
    except Exception:
        return []


def save_recent_projects(records: list[ProjectRecord]) -> None:
    APP_STATE_DIR.mkdir(parents=True, exist_ok=True)

    with open(RECENTS_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, indent=2)


def add_recent_project(record: ProjectRecord) -> None:
    records = load_recent_projects()
    records = [r for r in records if Path(r.path) != Path(record.path)]
    records.insert(0, record)
    save_recent_projects(records[:20])


def remove_recent_project(path: str) -> None:
    records = load_recent_projects()
    records = [r for r in records if Path(r.path) != Path(path)]
    save_recent_projects(records)


# =========================================================
# PROJECT CARD
# =========================================================

class ProjectCard(ctk.CTkFrame):
    """Custom class for project cards on the right side."""

    def __init__(
        self,
        master,
        name: str,
        project_id: str,
        path: str,
        log_callback,
        remove_callback,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.name = name
        self.project_id = project_id
        self.path = path
        self.log_callback = log_callback
        self.remove_callback = remove_callback

        self.grid_columnconfigure(0, weight=1)

        self.lbl_name = ctk.CTkLabel(self, text=name, font=("Arial", 16, "bold"))
        self.lbl_name.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.lbl_id = ctk.CTkLabel(self, text=f"id: {project_id}", font=("Arial", 12))
        self.lbl_id.grid(row=1, column=0, sticky="w", padx=10)

        self.lbl_path = ctk.CTkLabel(
            self,
            text=path,
            font=("Arial", 12, "italic"),
            text_color="gray"
        )
        self.lbl_path.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))

        self.btn_delete = ctk.CTkButton(
            self,
            text="X",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="#8b0000",
            command=self.destroy_card
        )
        self.btn_delete.grid(row=0, column=1, sticky="ne", padx=5, pady=5)

        # Open in VS Code when clicking the card
        self.bind("<Button-1>", self.open_project)
        self.lbl_name.bind("<Button-1>", self.open_project)
        self.lbl_id.bind("<Button-1>", self.open_project)
        self.lbl_path.bind("<Button-1>", self.open_project)

    def open_project(self, event=None):
        self.log_callback(f"Opening '{self.name}' in VS Code...")
        try:
            subprocess.Popen(["code", self.path])
            self.log_callback(f"Successfully launched: code {self.path}")
        except Exception as e:
            self.log_callback(f"Failed to open VS Code. {e}", is_error=True)

    def destroy_card(self):
        self.log_callback(f"Removed project card '{self.name}'.")
        self.remove_callback(self.path)
        self.destroy()



# =========================================================
# SCAFFOLD ENGINE----V1
# =========================================================


class ScaffoldEngineV1:
    def __init__(self, logCallback: LogCallback | None = None):
        self.logCallback = logCallback

        self.uiDependencies = [
            "tailwindcss",
            "@tailwindcss/vite",
            "class-variance-authority",
            "clsx",
            "tailwind-merge",
            "lucide-react",
            "tw-animate-css",
            "zod",
            "zustand",
            "serialport",
            "@serialport/parser-readline",
        ]

        self.shadcnComponents = [
            "button",
            "card",
            "input",
            "label",
            "dialog",
            "slider",
            "select",
            "switch",
            "sonner",
            "badge",
            "separator",
            "tabs",
            "drawer",
            "popover",

        ]

        self.addElectronUpdater = True
        self.useElectronDownloadMirror = False

    # =====================================================
    # LOGGING
    # =====================================================

    def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        source: str = "ENGINE",
    ) -> None:
        event = LogEvent(
            message=message,
            level=level,
            source=source,
        )

        if self.logCallback:
            self.logCallback(event)
        else:
            print(formatLogEvent(event), end="")

    def cleanTerminalText(self, text: str) -> str:
        return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)

    def patchElectronViteConfig(self, uiPath: Path) -> None:
        electronVitePath = uiPath / "electron.vite.config.ts"

        if not electronVitePath.exists():
            self.log(
                "electron.vite.config.ts not found. Skipping Vite config patch.",
                LogLevel.WARNING,
                "UI",
            )
            return

        try:
            content = electronVitePath.read_text(encoding="utf-8")
            changed = False

            # -------------------------------------------------
            # 1. Make sure tailwindcss Vite plugin is imported
            # -------------------------------------------------
            if "@tailwindcss/vite" not in content:
                content = content.replace(
                    "import react from '@vitejs/plugin-react'",
                    "import react from '@vitejs/plugin-react'\nimport tailwindcss from '@tailwindcss/vite'",
                )

                content = content.replace(
                    'import react from "@vitejs/plugin-react"',
                    'import react from "@vitejs/plugin-react"\nimport tailwindcss from "@tailwindcss/vite"',
                )

                changed = True

            # -------------------------------------------------
            # 2. Make sure renderer plugins include tailwindcss()
            # -------------------------------------------------
            if "tailwindcss()" not in content:
                content = re.sub(
                    r"plugins:\s*\[\s*react\(\)\s*\]",
                    "plugins: [react(), tailwindcss()]",
                    content,
                    count=1,
                )
                changed = True

            # -------------------------------------------------
            # 3. Make sure @ alias exists for Vite
            # -------------------------------------------------
            hasAtAlias = (
                    '"@": resolve("src/renderer/src")' in content
                    or "'@': resolve('src/renderer/src')" in content
                    or '"@": resolve(\'src/renderer/src\')' in content
                    or "'@': resolve(\"src/renderer/src\")" in content
            )

            if not hasAtAlias:
                # Case 1: template already has @renderer alias
                if "@renderer" in content:
                    content = re.sub(
                        r'(["\']@renderer["\']\s*:\s*resolve\(["\']src/renderer/src["\']\))',
                        r'\1,\n        "@": resolve("src/renderer/src")',
                        content,
                        count=1,
                    )
                    changed = True

                # Case 2: renderer block exists but has no resolve block
                elif "renderer:" in content:
                    content = re.sub(
                        r"(renderer\s*:\s*\{)",
                        r'''\1
                        resolve: {
                        alias: {
                            "@": resolve("src/renderer/src"),
                        },
                        },''',
                        content,
                        count=1,
                    )
                    changed = True

            # -------------------------------------------------
            # 4. Save final result
            # -------------------------------------------------
            if changed:
                electronVitePath.write_text(content, encoding="utf-8")
                self.log(
                    "Patched electron.vite.config.ts with @ alias and Tailwind plugin.",
                    LogLevel.SUCCESS,
                    "UI",
                )
            else:
                self.log(
                    "electron.vite.config.ts already has @ alias and Tailwind plugin.",
                    LogLevel.INFO,
                    "UI",
                )

        except Exception as error:
            self.log(
                f"Failed to patch electron.vite.config.ts: {error}",
                LogLevel.WARNING,
                "UI",
            )
    def classifyCommandLine(self, line: str) -> LogLevel:
        lowerLine = line.lower()

        errorWords = [
            "error",
            "failed",
            "exception",
            "traceback",
            "not found",
            "cannot",
            "could not",
            "no such file",
        ]

        warningWords = [
            "warning",
            "warn",
            "deprecated",
        ]

        successWords = [
            "done",
            "success",
            "completed",
            "finished",
            "created",
            "installed",
            "saved",
        ]

        if any(word in lowerLine for word in errorWords):
            return LogLevel.ERROR

        if any(word in lowerLine for word in warningWords):
            return LogLevel.WARNING

        if any(word in lowerLine for word in successWords):
            return LogLevel.SUCCESS

        return LogLevel.INFO

    def logCommandText(self, text: str, source: str = "CMD") -> None:
        cleanText = self.cleanTerminalText(text)

        for line in cleanText.splitlines():
            cleanLine = line.strip()

            if not cleanLine:
                continue

            level = self.classifyCommandLine(cleanLine)
            self.log(cleanLine, level, source)

    # =====================================================
    # COMMAND RUNNERS
    # =====================================================

    def runCommand(self, command: list[str], cwd: Path) -> None:
        commandText = " ".join(command)

        self.log(
            f"Running: {commandText}",
            LogLevel.COMMAND,
            "CMD",
        )

        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            if process.stdout:
                for line in process.stdout:
                    self.logCommandText(line, "CMD")

            returnCode = process.wait()

            if returnCode != 0:
                raise RuntimeError(
                    f"Command failed with exit code {returnCode}: {commandText}"
                )

            self.log(
                f"Finished: {commandText}",
                LogLevel.SUCCESS,
                "CMD",
            )

        except FileNotFoundError:
            self.log(
                f"Command not found: {command[0]}",
                LogLevel.ERROR,
                "CMD",
            )
            raise

    def runElectronCreateCommand(self, uiName: str, projectRoot: Path) -> None:
        try:
            import pexpect
        except ImportError:
            raise RuntimeError(
                "Missing Python package: pexpect. Install it with: python3 -m pip install pexpect"
            )

        self.log(
            f"Running interactive Electron scaffold: {uiName}",
            LogLevel.COMMAND,
            "CMD",
        )

        child = pexpect.spawn(
            "bunx",
            [
                "@quick-start/create-electron@latest",
                uiName,
                "--template",
                "react-ts",
            ],
            cwd=str(projectRoot),
            encoding="utf-8",
            timeout=240,
        )

        try:
            while True:
                result = child.expect(
                    [
                        r"Add Electron updater plugin\?",
                        r"Enable Electron download mirror proxy\?",
                        r"Scaffolding project in",
                        r"Done\.",
                        pexpect.EOF,
                        pexpect.TIMEOUT,
                    ]
                )

                self.logCommandText(child.before, "CMD")

                if result == 0:
                    if self.addElectronUpdater:
                        self.log(
                            "Prompt: Add Electron updater plugin → Yes",
                            LogLevel.INFO,
                            "CMD",
                        )
                        child.send("\x1b[C")
                        child.sendline("")
                    else:
                        self.log(
                            "Prompt: Add Electron updater plugin → No",
                            LogLevel.INFO,
                            "CMD",
                        )
                        child.sendline("")

                elif result == 1:
                    if self.useElectronDownloadMirror:
                        self.log(
                            "Prompt: Enable Electron download mirror proxy → Yes",
                            LogLevel.INFO,
                            "CMD",
                        )
                        child.send("\x1b[C")
                        child.sendline("")
                    else:
                        self.log(
                            "Prompt: Enable Electron download mirror proxy → No",
                            LogLevel.INFO,
                            "CMD",
                        )
                        child.sendline("")

                elif result == 2:
                    self.log(
                        "Electron scaffold started copying files...",
                        LogLevel.STEP,
                        "CMD",
                    )

                elif result == 3:
                    self.log(
                        "Electron scaffold reported Done.",
                        LogLevel.SUCCESS,
                        "CMD",
                    )

                elif result == 4:
                    break

                elif result == 5:
                    raise RuntimeError(
                        "Electron scaffold timed out while waiting for a prompt."
                    )

        finally:
            if child.isalive():
                child.close(force=True)
            else:
                child.close()

        if child.exitstatus not in (0, None):
            raise RuntimeError(
                f"Electron scaffold failed with exit code: {child.exitstatus}"
            )

        self.log(
            f"Finished interactive Electron scaffold: {uiName}",
            LogLevel.SUCCESS,
            "CMD",
        )

    # =====================================================
    # SAFE TEMPLATE OVERLAY
    # =====================================================

    def shouldIgnoreOverlayPath(self, relativePath: Path) -> bool:
        ignoredNames = {
            ".DS_Store",
            "__pycache__",
            "node_modules",
            "dist",
            "out",
            "build",
            ".git",
            ".pio",
        }

        return any(part in ignoredNames for part in relativePath.parts)

    def filesAreSame(self, sourcePath: Path, destinationPath: Path) -> bool:
        if not destinationPath.exists():
            return False

        return sourcePath.read_bytes() == destinationPath.read_bytes()

    def applyTemplateOverlay(
        self,
        source: Path,
        destination: Path,
        sourceName: str,
        allowUpdates: bool = True,
        protectedFiles: set[str] | None = None,
    ) -> None:
        protectedFiles = protectedFiles or set()

        if not source.exists():
            raise FileNotFoundError(f"{sourceName} template folder not found: {source}")

        createdCount = 0
        updatedCount = 0
        skippedCount = 0

        self.log(
            f"Applying {sourceName} template overlay...",
            LogLevel.STEP,
            sourceName,
        )

        for sourcePath in source.rglob("*"):
            relativePath = sourcePath.relative_to(source)

            if self.shouldIgnoreOverlayPath(relativePath):
                skippedCount += 1
                continue

            destinationPath = destination / relativePath
            relativeText = relativePath.as_posix()

            if sourcePath.is_dir():
                destinationPath.mkdir(parents=True, exist_ok=True)
                continue

            if relativeText in protectedFiles:
                self.log(
                    f"Skipped protected file: {relativeText}",
                    LogLevel.WARNING,
                    sourceName,
                )
                skippedCount += 1
                continue

            destinationPath.parent.mkdir(parents=True, exist_ok=True)

            if not destinationPath.exists():
                shutil.copy2(sourcePath, destinationPath)
                createdCount += 1
                continue

            if self.filesAreSame(sourcePath, destinationPath):
                skippedCount += 1
                continue

            if not allowUpdates:
                self.log(
                    f"Skipped existing file: {relativeText}",
                    LogLevel.WARNING,
                    sourceName,
                )
                skippedCount += 1
                continue

            shutil.copy2(sourcePath, destinationPath)
            updatedCount += 1

        self.log(
            f"{sourceName} overlay complete. Created: {createdCount}, Updated: {updatedCount}, Skipped: {skippedCount}",
            LogLevel.SUCCESS,
            sourceName,
        )

    # =====================================================
    # MAIN ENTRY POINT
    # =====================================================

    def create_project(self, spec: ProjectSpec) -> Path:
        return self.createProject(spec)

    def createProject(self, spec: ProjectSpec) -> Path:
        root = Path(spec.destination_root).expanduser().resolve()

        self.log("Validating destination folder...", LogLevel.STEP)

        if not root.exists():
            raise FileNotFoundError(f"Destination folder does not exist: {root}")

        if not root.is_dir():
            raise NotADirectoryError(f"Destination is not a folder: {root}")

        projectRoot = root / spec.project_slug

        if projectRoot.exists():
            raise FileExistsError(f"Project folder already exists: {projectRoot}")

        self.log(
            f"Creating project root: {projectRoot}",
            LogLevel.STEP,
        )

        projectRoot.mkdir(parents=True, exist_ok=False)

        try:
            self.scaffoldProject(spec, projectRoot)
        except Exception as error:
            self.log(
                f"Scaffold stopped. Partial project folder left here: {projectRoot}",
                LogLevel.WARNING,
                "ENGINE",
            )
            raise error

        self.log(
            f"Project scaffold completed: {projectRoot}",
            LogLevel.SUCCESS,
        )

        return projectRoot

    # =====================================================
    # PROJECT STRUCTURE
    # =====================================================

    def scaffoldProject(self, spec: ProjectSpec, projectRoot: Path) -> None:
        uiName = f"ui_{spec.project_slug}"
        espName = f"esp_{spec.project_slug}"

        uiPath = projectRoot / uiName
        espPath = projectRoot / espName
        metaDir = projectRoot / ".scaffold"

        self.scaffoldUi(spec, projectRoot, uiName, uiPath)
        self.scaffoldEsp32(espPath)
        self.writeMetadata(spec, projectRoot, uiPath, espPath, metaDir)

    # =====================================================
    # UI / ELECTRON
    # =====================================================

    def scaffoldUi(
        self,
        spec: ProjectSpec,
        projectRoot: Path,
        uiName: str,
        uiPath: Path,
    ) -> None:
        self.log(
            f"Creating Electron UI project: {uiName}",
            LogLevel.STEP,
            "UI",
        )

        self.runElectronCreateCommand(uiName, projectRoot)

        self.logFolderContents(projectRoot, "Project root after Electron CLI")

        if not uiPath.exists():
            children = [child.name for child in projectRoot.iterdir()]

            raise RuntimeError(
                f"UI folder was not created.\n"
                f"Expected: {uiPath}\n"
                f"Found in project root: {children}"
            )

        protectedUiFiles = {
            "package.json",
            "bun.lock",
            "electron.vite.config.ts",
            "electron-builder.yml",
            "dev-app-update.yml",
        }

        self.applyTemplateOverlay(
            source=UI_TEMPLATE_FILES_DIR,
            destination=uiPath,
            sourceName="UI",
            allowUpdates=True,
            protectedFiles=protectedUiFiles,
        )

        self.patchUiProjectFiles(spec, uiPath)

        self.log(
            "Installing Electron/UI dependencies...",
            LogLevel.STEP,
            "UI",
        )

        self.runCommand(
            ["bun", "install"],
            cwd=uiPath,
        )

        self.log(
            "Installing UI architecture dependencies...",
            LogLevel.STEP,
            "UI",
        )

        self.runCommand(
            ["bun", "add", *self.uiDependencies],
            cwd=uiPath,
        )

        self.log(
            "Generating shadcn/ui components...",
            LogLevel.STEP,
            "UI",
        )

        self.runCommand(
            [
                "bunx",
                "--bun",
                "shadcn@latest",
                "add",
                *self.shadcnComponents,
                "-y",
            ],
            cwd=uiPath,
        )

        self.log(
            "UI scaffold completed.",
            LogLevel.SUCCESS,
            "UI",
        )

    def patchUiProjectFiles(self, spec: ProjectSpec, uiPath: Path) -> None:
        self.patchPackageJson(spec, uiPath)
        self.patchElectronBuilderConfig(spec, uiPath)
        self.patchElectronViteConfig(uiPath)

    def patchPackageJson(self, spec: ProjectSpec, uiPath: Path) -> None:
        packageJsonPath = uiPath / "package.json"

        if not packageJsonPath.exists():
            self.log(
                "package.json not found. Skipping package patch.",
                LogLevel.WARNING,
                "UI",
            )
            return

        try:
            with open(packageJsonPath, "r", encoding="utf-8") as file:
                packageData = json.load(file)

            packageData["name"] = f"ui-{spec.project_slug}"
            packageData["productName"] = spec.name

            with open(packageJsonPath, "w", encoding="utf-8") as file:
                json.dump(packageData, file, indent=2)

            self.log(
                "Patched package.json name/productName.",
                LogLevel.SUCCESS,
                "UI",
            )

        except Exception as error:
            self.log(
                f"Failed to patch package.json: {error}",
                LogLevel.WARNING,
                "UI",
            )

    def patchElectronBuilderConfig(self, spec: ProjectSpec, uiPath: Path) -> None:
        electronBuilderPath = uiPath / "electron-builder.yml"

        if not electronBuilderPath.exists():
            self.log(
                "electron-builder.yml not found. Skipping builder patch.",
                LogLevel.WARNING,
                "UI",
            )
            return

        try:
            content = electronBuilderPath.read_text(encoding="utf-8")

            if re.search(r"(?m)^productName:", content):
                content = re.sub(
                    r"(?m)^productName:.*$",
                    f"productName: {spec.name}",
                    content,
                )
            else:
                content = f"productName: {spec.name}\n{content}"

            electronBuilderPath.write_text(content, encoding="utf-8")

            self.log(
                "Patched electron-builder.yml productName.",
                LogLevel.SUCCESS,
                "UI",
            )

        except Exception as error:
            self.log(
                f"Failed to patch electron-builder.yml: {error}",
                LogLevel.WARNING,
                "UI",
            )

    # =====================================================
    # ESP32 / PLATFORMIO TEMPLATE
    # =====================================================

    def scaffoldEsp32(self, espPath: Path) -> None:
        self.log(
            f"Creating ESP32 project: {espPath.name}",
            LogLevel.STEP,
            "ESP32",
        )

        espPath.mkdir(parents=True, exist_ok=False)

        if not ESP32_TEMPLATE_FILES_DIR.exists():
            raise FileNotFoundError(
                f"ESP32 template folder not found: {ESP32_TEMPLATE_FILES_DIR}"
            )

        self.applyTemplateOverlay(
            source=ESP32_TEMPLATE_FILES_DIR,
            destination=espPath,
            sourceName="ESP32",
            allowUpdates=True,
            protectedFiles=set(),
        )

        platformioIniPath = espPath / "platformio.ini"

        if not platformioIniPath.exists():
            raise RuntimeError(
                f"ESP32 scaffold failed. Missing platformio.ini at: {platformioIniPath}"
            )

        self.log(
            "ESP32 scaffold completed.",
            LogLevel.SUCCESS,
            "ESP32",
        )

    # =====================================================
    # METADATA
    # =====================================================

    def writeMetadata(
        self,
        spec: ProjectSpec,
        projectRoot: Path,
        uiPath: Path,
        espPath: Path,
        metaDir: Path,
    ) -> None:
        self.log(
            "Writing scaffold metadata...",
            LogLevel.STEP,
            "META",
        )

        metaDir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "name": spec.name,
            "project_id": spec.project_id,
            "project_slug": spec.project_slug,
            "project_root": str(projectRoot),
            "ui_path": str(uiPath),
            "esp32_path": str(espPath),
            "type": "ui_and_esp32",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        metadataPath = metaDir / "project.json"

        with open(metadataPath, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        self.log(
            f"Metadata written: {metadataPath}",
            LogLevel.SUCCESS,
            "META",
        )

    # =====================================================
    # DEBUG HELPERS
    # =====================================================

    def logFolderContents(self, folderPath: Path, label: str) -> None:
        if not folderPath.exists():
            self.log(
                f"{label}: folder does not exist: {folderPath}",
                LogLevel.WARNING,
                "DEBUG",
            )
            return

        children = [child.name for child in folderPath.iterdir()]

        self.log(
            f"{label}: {children}",
            LogLevel.INFO,
            "DEBUG",
        )
class ScaffolderApp(ctk.CTk):
    """Main Application Window"""

    def __init__(self):
        super().__init__()

        self.title("Electron & ESP32 Scaffolder")
        self.geometry("900x600")

        self.scaffoldEngine = ScaffoldEngineV1(
            logCallback=self.handleEngineLog
        )

        # Main Grid Layout
        self.grid_columnconfigure(0, weight=1, uniform="group1")
        self.grid_columnconfigure(1, weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # LEFT PANEL
        # ==========================================
        self.leftFrame = ctk.CTkFrame(self)
        self.leftFrame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.leftFrame.grid_columnconfigure(0, weight=1)

        self.settingsTitleLabel = ctk.CTkLabel(
            self.leftFrame,
            text="Project Settings",
            font=("Arial", 24, "bold")
        )
        self.settingsTitleLabel.grid(row=0, column=0, pady=(20, 20))

        self.projectNameEntry = ctk.CTkEntry(
            self.leftFrame,
            placeholder_text="Project Name",
            height=35
        )
        self.projectNameEntry.grid(row=1, column=0, padx=40, pady=10, sticky="ew")

        self.folderRow = ctk.CTkFrame(self.leftFrame, fg_color="transparent")
        self.folderRow.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        self.folderRow.grid_columnconfigure(0, weight=1)

        self.folderLocationEntry = ctk.CTkEntry(
            self.folderRow,
            placeholder_text="Folder Location",
            height=35
        )
        self.folderLocationEntry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.browseFolderButton = ctk.CTkButton(
            self.folderRow,
            text="Browse",
            width=90,
            height=35,
            command=self.browseFolder
        )
        self.browseFolderButton.grid(row=0, column=1)

        self.generateButton = ctk.CTkButton(
            self.leftFrame,
            text="Generate",
            height=40,
            font=("Arial", 14, "bold"),
            command=self.handleGenerate
        )
        self.generateButton.grid(row=3, column=0, padx=40, pady=20)

        self.logsTitleLabel = ctk.CTkLabel(
            self.leftFrame,
            text="Logs",
            font=("Arial", 14, "bold")
        )
        self.logsTitleLabel.grid(row=4, column=0, sticky="w", padx=40)

        self.logsTextbox = ctk.CTkTextbox(
            self.leftFrame,
            state="disabled",
            wrap="word"
        )
        self.logsTextbox.grid(row=5, column=0, padx=40, pady=(0, 20), sticky="nsew")
        self.leftFrame.grid_rowconfigure(5, weight=1)

        # ==========================================
        # RIGHT PANEL
        # ==========================================
        self.rightFrame = ctk.CTkFrame(self, fg_color="transparent")
        self.rightFrame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.rightFrame.grid_columnconfigure(0, weight=1)
        self.rightFrame.grid_rowconfigure(1, weight=1)

        self.projectsTitleLabel = ctk.CTkLabel(
            self.rightFrame,
            text="Recent Projects",
            font=("Arial", 24, "bold")
        )
        self.projectsTitleLabel.grid(row=0, column=0, pady=(20, 20))

        self.projectsFrame = ctk.CTkScrollableFrame(
            self.rightFrame,
            fg_color="transparent"
        )
        self.projectsFrame.grid(row=1, column=0, sticky="nsew")

        self.log("Scaffolder initialized and ready.", LogLevel.SUCCESS)
        self.loadRecentProjectCards()

    # ==========================================
    # LOGGING
    # ==========================================

    def handleEngineLog(self, event: LogEvent) -> None:
        self.after(
            0,
            lambda savedEvent=event: self.writeLogEvent(savedEvent)
        )

    def writeLogEvent(self, event: LogEvent) -> None:
        fullMessage = formatLogEvent(event)

        self.logsTextbox.configure(state="normal")
        self.logsTextbox.insert("end", fullMessage)
        self.logsTextbox.see("end")
        self.logsTextbox.configure(state="disabled")

    def log(
        self,
        message: str,
        level: LogLevel = LogLevel.INFO,
        source: str = "UI",
        is_error: bool = False,
    ) -> None:
        if is_error:
            level = LogLevel.ERROR

        event = LogEvent(
            message=message,
            level=level,
            source=source,
        )

        self.writeLogEvent(event)

    # ==========================================
    # UI ACTIONS
    # ==========================================

    def browseFolder(self) -> None:
        selectedFolder = filedialog.askdirectory(title="Select Project Destination")

        if selectedFolder:
            self.folderLocationEntry.delete(0, "end")
            self.folderLocationEntry.insert(0, selectedFolder)
            self.log(f"Selected folder: {selectedFolder}", LogLevel.INFO)

    def loadRecentProjectCards(self) -> None:
        for child in self.projectsFrame.winfo_children():
            child.destroy()

        for project in load_recent_projects():
            self.addProjectCard(project.name, project.project_id, project.path)

    def handleGenerate(self) -> None:
        name = self.projectNameEntry.get().strip()
        destination = self.folderLocationEntry.get().strip()

        if not name or not destination:
            self.log(
                "Generation failed: Missing Project Name or Folder Location.",
                LogLevel.ERROR,
            )
            self.showErrorPopup(
                "Input Error",
                "Please provide both a Project Name and a Folder Location before generating.",
            )
            return

        slug = slugify(name)

        if not slug:
            self.log(
                "Generation failed: Invalid project name.",
                LogLevel.ERROR,
            )
            self.showErrorPopup(
                "Input Error",
                "Project name must contain usable letters or numbers.",
            )
            return

        projectId = make_project_id(slug)

        spec = ProjectSpec(
            name=name,
            destination_root=destination,
            project_id=projectId,
            project_slug=slug,
        )

        self.generateButton.configure(state="disabled")

        self.log(
            f"Starting scaffold for '{name}'...",
            LogLevel.STEP,
        )

        def worker():
            try:
                projectRoot = self.scaffoldEngine.create_project(spec)

                record = ProjectRecord(
                    name=spec.name,
                    project_id=spec.project_id,
                    path=str(projectRoot),
                )

                add_recent_project(record)

                self.after(
                    0,
                    lambda: self.log(
                        f"Successfully generated '{name}' at '{projectRoot}'",
                        LogLevel.SUCCESS,
                    ),
                )

                self.after(
                    0,
                    lambda: self.addProjectCard(
                        spec.name,
                        spec.project_id,
                        str(projectRoot),
                    ),
                )

                self.after(
                    0,
                    lambda: self.projectNameEntry.delete(0, "end"),
                )

                self.after(
                    0,
                    lambda: self.folderLocationEntry.delete(0, "end"),
                )

            except Exception as error:
                errorMessage = str(error)

                self.after(
                    0,
                    lambda: self.log(
                        f"Generation failed: {errorMessage}",
                        LogLevel.ERROR,
                    ),
                )

                self.after(
                    0,
                    lambda: self.showErrorPopup(
                        "Scaffold Error",
                        errorMessage,
                    ),
                )

            finally:
                self.after(
                    0,
                    lambda: self.generateButton.configure(state="normal"),
                )

        threading.Thread(target=worker, daemon=True).start()

    def addProjectCard(self, name: str, projectId: str, path: str) -> None:
        card = ProjectCard(
            self.projectsFrame,
            name,
            projectId,
            path,
            self.log,
            self.removeProjectCard,
        )
        card.pack(fill="x", padx=20, pady=5)

    def removeProjectCard(self, path: str) -> None:
        remove_recent_project(path)

    def showErrorPopup(self, title: str, message: str) -> None:
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("350x150")
        popup.attributes("-topmost", True)

        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=1)

        popupMessageLabel = ctk.CTkLabel(
            popup,
            text=message,
            wraplength=300,
        )
        popupMessageLabel.grid(row=0, column=0, padx=20, pady=20)

        acknowledgeButton = ctk.CTkButton(
            popup,
            text="Acknowledge",
            command=popup.destroy,
        )
        acknowledgeButton.grid(row=1, column=0, pady=(0, 20))

if __name__ == "__main__":
    app = ScaffolderApp()
    app.mainloop()