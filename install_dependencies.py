#!/usr/bin/env python3
"""
Script de instalación de dependencias para RemoverAudioAI
Este script instala todas las dependencias necesarias para ejecutar la aplicación.
"""

import subprocess
import sys


def install_dependencies():
    print("Instalando dependencias de RemoverAudioAI...")
    print("-" * 50)

    # Instalar usando uv (si está disponible) o pip
    try:
        subprocess.run(["uv", "sync"], check=True, capture_output=True)
        print("Dependencias instaladas exitosamente con uv!")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("uv no encontrado, usando pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("Dependencias instaladas exitosamente con pip!")

    print("-" * 50)
    print("Instalación completada!")
    print("\nPara ejecutar la aplicación:")
    print("  python main.py")
    print("\nPara desarrollar (con herramientas de desarrollo):")
    print("  uv sync --all-extras")


if __name__ == "__main__":
    install_dependencies()
