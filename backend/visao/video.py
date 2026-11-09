"""Leitura de informações do vídeo e escrita de MP4 (H.264) com o FFmpeg do pacote imageio-ffmpeg."""
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
_PARES = "scale=trunc(iw/2)*2:trunc(ih/2)*2"   # H.264 (yuv420p) exige largura e altura pares


def ler_info(caminho):
    """{fps, total_frames, largura, altura, duracao} ou ValueError se o vídeo não puder ser lido."""
    cap = cv2.VideoCapture(str(caminho))
    try:
        if not cap.isOpened():
            raise ValueError("Não foi possível abrir o vídeo.")
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    finally:
        cap.release()
    if not (0 < fps <= 240) or total <= 0 or largura <= 0 or altura <= 0:
        raise ValueError("Não foi possível ler FPS, duração ou resolução do vídeo.")
    return {"fps": round(fps, 3), "total_frames": total, "largura": largura, "altura": altura,
            "duracao": round(total / fps, 3)}


def converter_h264(entrada, saida):
    """Converte qualquer vídeo aceito para MP4 H.264 com FPS constante, sem áudio.

    Garante que o navegador consiga reproduzir (ex.: vídeos HEVC de celular) e que
    número do frame / tempo fiquem consistentes (vídeos de celular costumam ter FPS variável).
    """
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(entrada),
           "-map", "0:v:0", "-an", "-vf", _PARES, "-fps_mode", "cfr",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(saida)]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=1800)
    if proc.returncode != 0 or not saida.is_file() or saida.stat().st_size == 0:
        raise RuntimeError("Falha ao converter o vídeo: " + (proc.stderr or "")[-800:])
    return saida


class EscritorVideo:
    """Recebe frames BGR (numpy) um a um e grava um MP4 H.264 reproduzível no navegador."""

    def __init__(self, saida, largura, altura, fps):
        self.saida = Path(saida)
        self.saida.parent.mkdir(parents=True, exist_ok=True)
        self.log = self.saida.with_suffix(".ffmpeg.log")
        self._log_fh = open(self.log, "w", encoding="utf-8", errors="replace")
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{largura}x{altura}", "-r", str(fps), "-i", "-",
               "-vf", _PARES, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(self.saida)]
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self._log_fh)

    def escrever(self, frame):
        self._proc.stdin.write(frame.tobytes())

    def fechar(self):
        self._proc.stdin.close()
        codigo = self._proc.wait(timeout=1800)
        self._log_fh.close()
        if codigo != 0 or not self.saida.is_file() or self.saida.stat().st_size == 0:
            raise RuntimeError("Falha ao gerar o vídeo anotado: " + self.log.read_text(errors="replace")[-800:])
        self.log.unlink(missing_ok=True)

    def abortar(self):
        try:
            self._proc.kill()
            self._proc.wait(timeout=10)
        except Exception:
            pass
        self._log_fh.close()
        self.saida.unlink(missing_ok=True)
