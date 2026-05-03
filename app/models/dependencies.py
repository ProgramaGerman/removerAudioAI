class DependencyChecker:
    REQUIRED_PACKAGES: list[str] = [
        "customtkinter",
        "demucs",
        "torch",
        "torchaudio",
        "PIL",
        "dotenv",
        "httpx",
    ]

    SYSTEM_DEPENDENCIES: list[str] = [
        "ffmpeg",
    ]

    def __init__(self) -> None:
        self._missing_packages: list[str] = []
        self._missing_system: list[str] = []

    def check_packages(self) -> bool:
        self._missing_packages = []
        for package in self.REQUIRED_PACKAGES:
            module_name = package.replace("-", "_")
            try:
                __import__(module_name)
            except ImportError:
                self._missing_packages.append(package)
        return len(self._missing_packages) == 0

    def check_system_dependencies(self) -> bool:
        import shutil

        self._missing_system = []
        for cmd in self.SYSTEM_DEPENDENCIES:
            if shutil.which(cmd) is None:
                self._missing_system.append(cmd)
        return len(self._missing_system) == 0

    def get_missing_packages(self) -> list[str]:
        return self._missing_packages.copy()

    def get_missing_system(self) -> list[str]:
        return self._missing_system.copy()

    def is_all_installed(self) -> bool:
        return self.check_packages() and self.check_system_dependencies()

    def get_install_command(self) -> str:
        missing = self.get_missing_packages()
        if missing:
            return f"uv add {' '.join(missing)}"
        return ""

    def get_system_install_instructions(self) -> list[str]:
        instructions = []
        if "ffmpeg" in self._missing_system:
            instructions.append(
                "FFmpeg es requerido. Instala desde: https://ffmpeg.org/download.html"
            )
            instructions.append("En Windows: winget install FFmpeg")
            instructions.append("En macOS: brew install ffmpeg")
            instructions.append("En Linux: sudo apt install ffmpeg")
        return instructions
