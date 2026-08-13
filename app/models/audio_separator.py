import os
from pathlib import Path


class AudioSeparator:
    DEMUCS_MODEL: str = "htdemucs"

    def __init__(self) -> None:
        self._model = None
        self._device = "cuda" if self._check_cuda() else "cpu"

    def _check_cuda(self) -> bool:
        try:
            import torch

            return torch.cuda.is_available()
        except Exception:
            return False

    def load_model(self) -> None:
        try:
            from demucs import pretrained

            self._model = pretrained.get_model(self.DEMUCS_MODEL)
            self._model.to(self._device)
            self._model.eval()
        except Exception as e:
            raise RuntimeError(f"Error al cargar modelo Demucs: {e}") from e

    # Formatos que libsndfile/soundfile NO puede decodificar directamente
    # y que por lo tanto necesitan pasar antes por ffmpeg.
    _FFMPEG_REQUIRED_EXTENSIONS = {".m4a", ".aac", ".mp4", ".mp3"}

    def _transcode_with_ffmpeg(self, audio_path: str) -> str:
        """Convierte un audio a WAV temporal usando ffmpeg.

        Necesario para contenedores/codecs que libsndfile no soporta,
        como .m4a/AAC.
        """
        import shutil
        import subprocess
        import tempfile

        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise RuntimeError(
                "ffmpeg no está instalado o no está en el PATH. Es necesario "
                "para leer archivos .m4a/.aac/.mp3. Instálalo desde "
                "https://ffmpeg.org/download.html"
            )

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(tmp_fd)

        result = subprocess.run(
            [ffmpeg_path, "-y", "-i", audio_path, "-ar", "44100", "-ac", "2", tmp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg no pudo convertir '{audio_path}': "
                f"{result.stderr.decode(errors='ignore')}"
            )
        return tmp_path

    def _load_audio(self, audio_path: str, target_channels: int, target_sr: int):
        """Carga audio con soundfile (sin dependencia en torchcodec).

        soundfile usa libsndfile directamente y no requiere torchcodec ni
        torchaudio 2.9+ como backend de decodificación. Para formatos que
        libsndfile no soporta (m4a, aac, mp3, mp4), se pre-convierte a WAV
        con ffmpeg de forma transparente.
        """
        import numpy as np
        import soundfile as sf
        import torch
        from pathlib import Path as _Path

        ext = _Path(audio_path).suffix.lower()
        temp_wav_path: str | None = None

        if ext in self._FFMPEG_REQUIRED_EXTENSIONS:
            temp_wav_path = self._transcode_with_ffmpeg(audio_path)
            audio_path = temp_wav_path

        try:
            # soundfile carga como [samples, channels] en float32/float64
            data, sr = sf.read(audio_path, always_2d=True, dtype="float32")
        except Exception as e:
            # Último recurso: si soundfile falla por cualquier otro motivo,
            # intentar igualmente vía ffmpeg antes de rendirse.
            if temp_wav_path is None:
                temp_wav_path = self._transcode_with_ffmpeg(audio_path)
                data, sr = sf.read(temp_wav_path, always_2d=True, dtype="float32")
            else:
                raise RuntimeError(f"No se pudo leer el audio convertido: {e}") from e
        finally:
            if temp_wav_path is not None and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except OSError:
                    pass

        # Transponer a [channels, samples] (formato torch)
        wav = torch.from_numpy(data.T)  # [C, T]

        # Resample si el sample rate no coincide
        if sr != target_sr:
            try:
                from math import gcd

                from scipy.signal import resample_poly

                g = gcd(target_sr, sr)
                up, down = target_sr // g, sr // g
                resampled = resample_poly(data, up, down, axis=0)
                wav = torch.from_numpy(resampled.T.astype(np.float32))
            except ImportError:
                # Fallback: resample simple con interpolación lineal
                ratio = target_sr / sr
                new_len = int(wav.shape[1] * ratio)
                wav_np = wav.numpy()
                x_old = np.linspace(0, 1, wav.shape[1])
                x_new = np.linspace(0, 1, new_len)
                resampled = np.array([np.interp(x_new, x_old, ch) for ch in wav_np])
                wav = torch.from_numpy(resampled.astype(np.float32))

        # Ajustar número de canales
        current_channels = wav.shape[0]
        if current_channels == 1 and target_channels == 2:
            wav = wav.repeat(2, 1)  # mono -> stereo
        elif current_channels > target_channels:
            wav = wav[:target_channels]  # recortar canales extra

        return wav.float()

    def _save_audio(self, wav_tensor, output_path: str, sample_rate: int) -> None:
        """Guarda audio con soundfile (sin dependencia en torchcodec)."""
        import soundfile as sf

        # wav_tensor: [C, T] float32 en rango [-1, 1]
        data = wav_tensor.numpy().T  # [T, C]
        sf.write(output_path, data, sample_rate, subtype="PCM_16")

    def separate(
        self,
        audio_path: str,
        output_dir: str,
        mode: str = "instrumental_only",
    ) -> dict[str, str]:
        if self._model is None:
            self.load_model()

        import torch
        from demucs.apply import apply_model

        # Cargar audio con soundfile — evita completamente torchcodec
        wav = self._load_audio(
            audio_path,
            self._model.audio_channels,
            self._model.samplerate,
        )

        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()

        with torch.no_grad():
            sources = apply_model(
                self._model,
                wav[None],
                device=self._device,
                shifts=1,
                split=True,
                overlap=0.25,
                progress=False,
            )[0]

        sources = sources * ref.std() + ref.mean()

        output_files = {}
        base_name = Path(audio_path).stem

        # Fuentes de htdemucs: drums, bass, other, vocals
        # El "instrumental" se construye sumando drums+bass+other
        source_dict = {name: src for src, name in zip(sources, self._model.sources)}

        os.makedirs(output_dir, exist_ok=True)

        if mode == "instrumental_only":
            # Sumar todas las fuentes excepto vocals
            instrumental_sources = [
                src for name, src in source_dict.items() if name != "vocals"
            ]
            if instrumental_sources:
                import torch
                instrumental = sum(instrumental_sources[1:], instrumental_sources[0].clone())
                instrumental = instrumental / max(1.01 * instrumental.abs().max().item(), 1.0)
                instrumental = instrumental.cpu()
                out_path = os.path.join(output_dir, f"{base_name}_instrumental.wav")
                self._save_audio(instrumental, out_path, self._model.samplerate)
                output_files["instrumental"] = out_path

        elif mode == "vocals_only":
            if "vocals" in source_dict:
                vocal_src = source_dict["vocals"]
                vocal_src = vocal_src / max(1.01 * vocal_src.abs().max().item(), 1.0)
                vocal_src = vocal_src.cpu()
                out_path = os.path.join(output_dir, f"{base_name}_vocals.wav")
                self._save_audio(vocal_src, out_path, self._model.samplerate)
                output_files["vocals"] = out_path

        else:  # "both" — generar instrumental + vocals como archivos separados
            # Instrumental (drums+bass+other)
            instrumental_sources = [
                src for name, src in source_dict.items() if name != "vocals"
            ]
            if instrumental_sources:
                import torch
                instrumental = sum(instrumental_sources[1:], instrumental_sources[0].clone())
                instrumental = instrumental / max(1.01 * instrumental.abs().max().item(), 1.0)
                instrumental = instrumental.cpu()
                out_path = os.path.join(output_dir, f"{base_name}_instrumental.wav")
                self._save_audio(instrumental, out_path, self._model.samplerate)
                output_files["instrumental"] = out_path

            # Vocals
            if "vocals" in source_dict:
                vocal_src = source_dict["vocals"]
                vocal_src = vocal_src / max(1.01 * vocal_src.abs().max().item(), 1.0)
                vocal_src = vocal_src.cpu()
                out_path = os.path.join(output_dir, f"{base_name}_vocals.wav")
                self._save_audio(vocal_src, out_path, self._model.samplerate)
                output_files["vocals"] = out_path

        return output_files

    def get_device(self) -> str:
        return self._device

    def is_model_loaded(self) -> bool:
        return self._model is not None
