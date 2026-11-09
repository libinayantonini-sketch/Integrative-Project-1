"""Configurações do back-end.

Os valores vêm do arquivo backend/.env (copie backend/.env.example para backend/.env
e preencha a senha do seu MySQL). Caminhos relativos são resolvidos a partir da pasta backend/.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parent
RAIZ = BACKEND.parent
load_dotenv(BACKEND / ".env")


def _caminho(nome, padrao):
    p = Path(os.getenv(nome) or padrao)
    return p if p.is_absolute() else (BACKEND / p).resolve()


# Banco de dados (MySQL). O nome do banco deve ser projeto_sinalizacoes (o mesmo dos scripts SQL).
DB_URL = os.getenv("DB_URL", "mysql+pymysql://root:@localhost:3306/projeto_sinalizacoes")

# Pastas e arquivos
STORAGE_DIR = _caminho("STORAGE_DIR", "storage")              # vídeos original e anotado
MODELO_PESOS = _caminho("MODELO_PESOS", "modelos/detector_v1.pt")
FRONTEND_DIR = _caminho("FRONTEND_DIR", "../frontend")         # a API também serve o front

# Servidor
HOST = os.getenv("HOST", "127.0.0.1")
PORTA = int(os.getenv("PORTA", "8000"))

# Processamento
INTERVALO_EXTRACAO_S = float(os.getenv("INTERVALO_EXTRACAO_S", "1"))  # 1 frame guardado a cada X segundos
QUALIDADE_JPEG = int(os.getenv("QUALIDADE_JPEG", "90"))
DISPOSITIVO = os.getenv("DISPOSITIVO") or None   # vazio = automático; "cpu" ou "0" (GPU)

# Regras de envio (as mesmas do front)
VIDEO_MIN_S = float(os.getenv("VIDEO_MIN_S", "10"))
VIDEO_MAX_S = float(os.getenv("VIDEO_MAX_S", "40"))
TAM_MAX_MB = int(os.getenv("TAM_MAX_MB", "200"))
FORMATOS_VIDEO = {".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv"}
