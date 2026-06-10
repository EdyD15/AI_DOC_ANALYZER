import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

# Calea fixa catre folderul aplicatiei (nu se schimba cand .exe e mutat pe Desktop)
APP_DIR = Path(r"d:\d downloads\AI_DOC_ANALIZER")
FRONTEND_DIR = APP_DIR / "frontend"


def load_env():
    env_file = APP_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


def main():
    load_env()

    CREATE_NEW_CONSOLE = 0x00000010

    # Backend FastAPI
    subprocess.Popen(
        "uvicorn api:app --reload --port 8000",
        cwd=str(APP_DIR),
        shell=True,
        creationflags=CREATE_NEW_CONSOLE,
    )

    # Frontend Vite
    subprocess.Popen(
        "npm run dev",
        cwd=str(FRONTEND_DIR),
        shell=True,
        creationflags=CREATE_NEW_CONSOLE,
    )

    # Asteapta serverele sa porneasca, apoi deschide browserul
    time.sleep(4)
    webbrowser.open("http://localhost:5173")


if __name__ == "__main__":
    main()
