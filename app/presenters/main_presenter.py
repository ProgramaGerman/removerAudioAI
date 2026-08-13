import os
import threading
from collections.abc import Callable

from app.models.audio_separator import AudioSeparator
from app.models.dependencies import DependencyChecker
from app.models.file_handler import FileHandler


class MainPresenter:
    def __init__(self) -> None:
        self._dependency_checker = DependencyChecker()
        self._file_handler = FileHandler()
        self._audio_separator = AudioSeparator()
        self._is_processing = False
        self._current_mode = "instrumental_only"
        self._output_directory: str | None = None
        self._callbacks: dict[str, Callable] = {}

    def set_callback(self, event: str, callback: Callable) -> None:
        self._callbacks[event] = callback

    def _emit(self, event: str, *args, **kwargs) -> None:
        if event in self._callbacks:
            self._callbacks[event](*args, **kwargs)

    def check_dependencies(self) -> bool:
        return self._dependency_checker.is_all_installed()

    def get_missing_packages(self) -> list[str]:
        return self._dependency_checker.get_missing_packages()

    def get_missing_system(self) -> list[str]:
        return self._dependency_checker.get_missing_system()

    def install_packages(self) -> None:
        """Inicia la instalación de paquetes faltantes en un hilo separado.

        Usa `uv add`, ya que este proyecto se gestiona con uv. Los entornos
        virtuales creados por uv no siempre incluyen pip, así que depender
        de `python -m pip` aquí puede fallar silenciosamente.
        """
        import shutil
        import threading

        missing = self.get_missing_packages()
        if not missing:
            self._emit("install_complete", True)
            return

        def _install():
            import subprocess

            uv_path = shutil.which("uv")
            if uv_path is None:
                self._emit(
                    "install_error",
                    "No se encontró 'uv' en el PATH. Instálalo desde "
                    "https://docs.astral.sh/uv/getting-started/installation/ "
                    f"y luego ejecuta: uv add {' '.join(missing)}",
                )
                return

            try:
                self._emit("install_progress", f"Instalando con uv: {', '.join(missing)}...")
                process = subprocess.Popen(
                    [uv_path, "add"] + missing,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        self._emit("install_progress", line)
                process.wait()
                if process.returncode == 0:
                    self._emit("install_complete", True)
                else:
                    self._emit(
                        "install_error", f"uv add terminó con código {process.returncode}"
                    )
            except Exception as e:
                self._emit("install_error", str(e))

        thread = threading.Thread(target=_install, daemon=True)
        thread.start()

    def set_output_directory(self, path: str | None) -> None:
        self._output_directory = path

    def get_output_directory(self) -> str | None:
        return self._output_directory

    def set_mode(self, mode: str) -> None:
        valid_modes = ["instrumental_only", "vocals_only", "both"]
        if mode in valid_modes:
            self._current_mode = mode

    def get_mode(self) -> str:
        return self._current_mode

    def is_processing(self) -> bool:
        return self._is_processing

    def get_device(self) -> str:
        return self._audio_separator.get_device()

    def process_file(self, file_path: str) -> None:
        if self._is_processing:
            return
        if not self._file_handler.is_supported(file_path):
            self._emit("error", "Archivo no soportado")
            return

        self._is_processing = True
        self._emit("processing_started")

        thread = threading.Thread(target=self._process_in_thread, args=(file_path,))
        thread.start()

    def _process_in_thread(self, file_path: str) -> None:
        try:
            audio_path = file_path
            if self._file_handler.is_video_file(file_path):
                self._emit("status", "Extrayendo audio del video...")
                audio_path = self._file_handler.extract_audio_from_video(file_path)

            output_dir = self._output_directory or os.path.dirname(file_path)

            self._emit("status", "Separando fuentes de audio...")
            output_files = self._audio_separator.separate(
                audio_path,
                output_dir,
                self._current_mode,
            )

            if self._file_handler.is_video_file(file_path):
                self._file_handler.cleanup_temp_audio()

            self._emit("processing_complete", output_files)
        except Exception as e:
            self._emit("error", str(e))
        finally:
            self._is_processing = False
            self._emit("processing_finished")

    def cancel_processing(self) -> None:
        self._is_processing = False
