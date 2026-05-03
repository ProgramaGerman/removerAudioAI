import os
from pathlib import Path

import ffmpeg


class FileHandler:
    AUDIO_EXTENSIONS: set[str] = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
    VIDEO_EXTENSIONS: set[str] = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv"}

    def __init__(self) -> None:
        self._temp_audio_path: str | None = None

    def is_audio_file(self, path: str) -> bool:
        ext = Path(path).suffix.lower()
        return ext in self.AUDIO_EXTENSIONS

    def is_video_file(self, path: str) -> bool:
        ext = Path(path).suffix.lower()
        return ext in self.VIDEO_EXTENSIONS

    def is_supported(self, path: str) -> bool:
        return self.is_audio_file(path) or self.is_video_file(path)

    def get_file_type(self, path: str) -> str:
        if self.is_audio_file(path):
            return "audio"
        if self.is_video_file(path):
            return "video"
        return "unsupported"

    def extract_audio_from_video(self, video_path: str, output_path: str | None = None) -> str:
        if not self.is_video_file(video_path):
            raise ValueError(f"El archivo no es un video válido: {video_path}")

        if output_path is None:
            base_name = Path(video_path).stem
            output_path = os.path.join(os.path.dirname(video_path), f"{base_name}_audio.wav")

        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, output_path, acodec="pcm_s16le", ar=44100)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            self._temp_audio_path = output_path
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"Error al extraer audio: {e.stderr.decode()}") from e

    def get_output_filename(
        self, original_path: str, mode: str, output_dir: str | None = None
    ) -> str:
        base_name = Path(original_path).stem
        if output_dir is None:
            output_dir = os.path.dirname(original_path)

        if mode == "instrumental_only":
            filename = f"{base_name}_instrumental.wav"
        elif mode == "vocals_only":
            filename = f"{base_name}_vocals.wav"
        else:
            filename = f"{base_name}_separated.wav"

        return os.path.join(output_dir, filename)

    def ensure_output_directory(self, path: str) -> None:
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def cleanup_temp_audio(self) -> None:
        if self._temp_audio_path and os.path.exists(self._temp_audio_path):
            try:
                os.remove(self._temp_audio_path)
            except OSError:
                pass
        self._temp_audio_path = None
