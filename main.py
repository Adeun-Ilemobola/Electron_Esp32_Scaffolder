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

# =========================================================
# PATHS / CONSTANTS
# =========================================================

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"

# Match your current folder names exactly
UI_TEMPLATE_DIR = TEMPLATES_DIR / "Command_Center_App"
ESP32_TEMPLATE_DIR = TEMPLATES_DIR / "esp32"

APP_STATE_DIR = Path.home() / ".electron_esp32_scaffolder"
RECENTS_FILE = APP_STATE_DIR / "recent_projects.json"

# Set up the overall theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


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
# SCAFFOLD ENGINE
# =========================================================

class ScaffoldEngine:
    def __init__(self, ui_template_dir: Path, esp32_template_dir: Path):
        self.ui_template_dir = ui_template_dir
        self.esp32_template_dir = esp32_template_dir

    def create_project(self, spec: ProjectSpec) -> Path:
        if not self.ui_template_dir.exists():
            raise FileNotFoundError(f"UI template folder not found: {self.ui_template_dir}")

        if not self.esp32_template_dir.exists():
            raise FileNotFoundError(f"ESP32 template folder not found: {self.esp32_template_dir}")

        root = Path(spec.destination_root).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"Destination folder does not exist: {root}")

        if not root.is_dir():
            raise NotADirectoryError(f"Destination is not a folder: {root}")

        project_root = root / spec.project_slug
        ui_target = project_root / f'UI_{spec.name}'
        esp32_target = project_root / f"esp_{spec.name}"
        meta_dir = project_root / ".scaffold"

        if project_root.exists():
            raise FileExistsError(f"Project folder already exists: {project_root}")

        project_root.mkdir(parents=True, exist_ok=False)

        shutil.copytree(self.ui_template_dir, ui_target)
        # make the package.json  name key  value  change
        package_json = ui_target / "package.json"
        if package_json.exists():
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["name"] = f"UI_{spec.name}"
            with open(package_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        #update electron-builder.yml with new name
        electron_builder_yml = ui_target / "electron-builder.yml"
        if electron_builder_yml.exists():
            with open(electron_builder_yml, "r", encoding="utf-8") as f:
                content = f.read()
                if re.search(r"productName: .+", content):
                    content = re.sub(r"productName: .+", f"productName: {spec.name}", content)
                
            with open(electron_builder_yml, "w", encoding="utf-8") as f:
                f.write(content)
        


        shutil.copytree(self.esp32_template_dir, esp32_target)

        self._clean_ui_template(ui_target)
        self._clean_esp32_template(esp32_target)
        self._patch_ui_template(ui_target, spec)

        meta_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "name": spec.name,
            "project_id": spec.project_id,
            "project_slug": spec.project_slug,
            "project_root": str(project_root),
            "ui_path": str(ui_target),
            "esp32_path": str(esp32_target),
            "type": "ui_and_esp32"
        }

        with open(meta_dir / "project.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return project_root

    def _safe_remove(self, target: Path) -> None:
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()

    def _clean_ui_template(self, ui_target: Path) -> None:
        for junk in ["node_modules", "out", "dist", "build", ".git", ".DS_Store"]:
            self._safe_remove(ui_target / junk)

    def _clean_esp32_template(self, esp32_target: Path) -> None:
        for junk in [".pio", ".git", ".DS_Store"]:
            self._safe_remove(esp32_target / junk)

    def _patch_ui_template(self, ui_target: Path, spec: ProjectSpec) -> None:
        package_json = ui_target / "package.json"

        if not package_json.exists():
            return

        try:
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["name"] = spec.project_slug
            data["productName"] = spec.name

            with open(package_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            # Non-fatal: scaffold should still succeed even if patching package.json fails
            pass


# =========================================================
# MAIN APP
# =========================================================

class ScaffolderApp(ctk.CTk):
    """Main Application Window"""

    def __init__(self):
        super().__init__()

        self.title("Electron & ESP32 Scaffolder")
        self.geometry("900x600")

        self.engine = ScaffoldEngine(UI_TEMPLATE_DIR, ESP32_TEMPLATE_DIR)

        # Main Grid Layout
        self.grid_columnconfigure(0, weight=1, uniform="group1")
        self.grid_columnconfigure(1, weight=1, uniform="group1")
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # LEFT PANEL
        # ==========================================
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.lbl_settings_title = ctk.CTkLabel(
            self.left_frame,
            text="Project Settings",
            font=("Arial", 24, "bold")
        )
        self.lbl_settings_title.grid(row=0, column=0, pady=(20, 20))

        self.entry_project_name = ctk.CTkEntry(
            self.left_frame,
            placeholder_text="Project Name",
            height=35
        )
        self.entry_project_name.grid(row=1, column=0, padx=40, pady=10, sticky="ew")

        self.folder_row = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.folder_row.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        self.folder_row.grid_columnconfigure(0, weight=1)

        self.entry_folder_location = ctk.CTkEntry(
            self.folder_row,
            placeholder_text="Folder Location",
            height=35
        )
        self.entry_folder_location.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.btn_browse_folder = ctk.CTkButton(
            self.folder_row,
            text="Browse",
            width=90,
            height=35,
            command=self.browse_folder
        )
        self.btn_browse_folder.grid(row=0, column=1)

        self.btn_generate = ctk.CTkButton(
            self.left_frame,
            text="Generate",
            height=40,
            font=("Arial", 14, "bold"),
            command=self.handle_generate
        )
        self.btn_generate.grid(row=3, column=0, padx=40, pady=20)

        self.lbl_logs_title = ctk.CTkLabel(
            self.left_frame,
            text="Logs",
            font=("Arial", 14, "bold")
        )
        self.lbl_logs_title.grid(row=4, column=0, sticky="w", padx=40)

        self.textbox_logs = ctk.CTkTextbox(
            self.left_frame,
            state="disabled",
            wrap="word"
        )
        self.textbox_logs.grid(row=5, column=0, padx=40, pady=(0, 20), sticky="nsew")
        self.left_frame.grid_rowconfigure(5, weight=1)

        # ==========================================
        # RIGHT PANEL
        # ==========================================
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)

        self.lbl_projects_title = ctk.CTkLabel(
            self.right_frame,
            text="Recent Projects",
            font=("Arial", 24, "bold")
        )
        self.lbl_projects_title.grid(row=0, column=0, pady=(20, 20))

        self.scrollable_projects_frame = ctk.CTkScrollableFrame(
            self.right_frame,
            fg_color="transparent"
        )
        self.scrollable_projects_frame.grid(row=1, column=0, sticky="nsew")

        # ==========================================
        # INITIALIZATION ROUTINES
        # ==========================================
        self.log("Scaffolder initialized and ready.")
        self.load_recent_project_cards()

    # ==========================================
    # LOGIC & METHODS
    # ==========================================
    def browse_folder(self) -> None:
        selected_folder = filedialog.askdirectory(title="Select Project Destination")

        if selected_folder:
            self.entry_folder_location.delete(0, "end")
            self.entry_folder_location.insert(0, selected_folder)
            self.log(f"Selected folder: {selected_folder}")
    def log(self, message: str, is_error: bool = False) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "ERROR" if is_error else "INFO"
        full_msg = f"[{timestamp}] {prefix}: {message}\n"

        self.textbox_logs.configure(state="normal")
        self.textbox_logs.insert("end", full_msg)
        self.textbox_logs.see("end")
        self.textbox_logs.configure(state="disabled")

    def load_recent_project_cards(self) -> None:
        for child in self.scrollable_projects_frame.winfo_children():
            child.destroy()

        for project in load_recent_projects():
            self.add_project_card(project.name, project.project_id, project.path)

    def handle_generate(self) -> None:
        name = self.entry_project_name.get().strip()
        destination = self.entry_folder_location.get().strip()

        if not name or not destination:
            self.log("Generation failed: Missing Project Name or Folder Location.", is_error=True)
            self.show_error_popup(
                "Input Error",
                "Please provide both a Project Name and a Folder Location before generating."
            )
            return

        slug = slugify(name)
        if not slug:
            self.log("Generation failed: Invalid project name.", is_error=True)
            self.show_error_popup(
                "Input Error",
                "Project name must contain usable letters or numbers."
            )
            return

        project_id = make_project_id(slug)
        spec = ProjectSpec(
            name=name,
            destination_root=destination,
            project_id=project_id,
            project_slug=slug,
        )

        self.btn_generate.configure(state="disabled")
        self.log(f"Starting scaffold for '{name}'...")

        def worker():
            try:
                project_root = self.engine.create_project(spec)

                record = ProjectRecord(
                    name=spec.name,
                    project_id=spec.project_id,
                    path=str(project_root),
                )
                add_recent_project(record)

                self.after(0, lambda: self.log(
                    f"Successfully generated '{name}' at '{project_root}'"
                ))
                self.after(0, lambda: self.add_project_card(
                    spec.name,
                    spec.project_id,
                    str(project_root)
                ))
                self.after(0, lambda: self.entry_project_name.delete(0, "end"))
                self.after(0, lambda: self.entry_folder_location.delete(0, "end"))

            except Exception as e:
                self.after(0, lambda: self.log(f"Generation failed: {e}", is_error=True))
                self.after(0, lambda: self.show_error_popup("Scaffold Error", str(e)))
            finally:
                self.after(0, lambda: self.btn_generate.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def add_project_card(self, name: str, proj_id: str, path: str) -> None:
        card = ProjectCard(
            self.scrollable_projects_frame,
            name,
            proj_id,
            path,
            self.log,
            self.remove_project_card
        )
        card.pack(fill="x", padx=20, pady=5)

    def remove_project_card(self, path: str) -> None:
        remove_recent_project(path)

    def show_error_popup(self, title: str, message: str) -> None:
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("350x150")
        popup.attributes("-topmost", True)

        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=1)

        lbl_popup_msg = ctk.CTkLabel(popup, text=message, wraplength=300)
        lbl_popup_msg.grid(row=0, column=0, padx=20, pady=20)

        btn_popup_ack = ctk.CTkButton(popup, text="Acknowledge", command=popup.destroy)
        btn_popup_ack.grid(row=1, column=0, pady=(0, 20))


if __name__ == "__main__":
    app = ScaffolderApp()
    app.mainloop()