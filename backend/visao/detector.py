"""Detector de placas (YOLO26) treinado no notebook notebooks/treino_detector_placas_yolo26.ipynb.

O modelo é o arquivo backend/modelos/detector_v1.pt. As configurações usadas no treino
(classes, imgsz, conf, iou, versão) vêm do detector_v1_info.json ao lado dele.

    det = DetectorPlacas("backend/modelos/detector_v1.pt")
    caixas = det.detectar(frame)      # frame = imagem BGR do OpenCV
    # -> [{"classe": "placa", "confianca": 0.93, "x_min": 120, "y_min": 55, "x_max": 190, "y_max": 160}]
"""
import json
from pathlib import Path
from threading import Lock

import cv2

VERDE = (0, 200, 0)


class DetectorPlacas:
    def __init__(self, pesos, dispositivo=None):
        pesos = Path(pesos)
        if not pesos.is_file():
            raise FileNotFoundError(
                f"Modelo não encontrado: {pesos}\n"
                "Copie o detector_v1.pt (gerado pelo notebook de treino) para backend/modelos/.")
        info_arq = pesos.with_name(pesos.stem + "_info.json")
        info = json.loads(info_arq.read_text(encoding="utf-8")) if info_arq.is_file() else {}

        from ultralytics import YOLO   # importado aqui para a API subir mais rápido quando há erro de config
        self.modelo = YOLO(str(pesos))
        self.nome = Path(info.get("pesos_base", "yolo26")).stem          # ex.: yolo26n
        self.versao = info.get("model_version", pesos.stem)              # ex.: detector_v1
        self.conf = float(info.get("conf", 0.25))
        self.iou = float(info.get("iou", 0.7))
        self.imgsz = int(info.get("imgsz", 640))
        self.dispositivo = dispositivo
        self.classes = self.modelo.names
        self._lock = Lock()   # o modelo não deve ser usado por duas threads ao mesmo tempo

    def detectar(self, frame_bgr):
        """Recebe um frame (BGR) e devolve a lista de caixas em pixels do frame original."""
        with self._lock:
            r = self.modelo.predict(frame_bgr, conf=self.conf, iou=self.iou, imgsz=self.imgsz,
                                    device=self.dispositivo, verbose=False)[0]
        h, w = frame_bgr.shape[:2]
        return [
            {"classe": self.classes[int(k)], "confianca": float(c),
             "x_min": max(0, int(round(x1))), "y_min": max(0, int(round(y1))),
             "x_max": min(w, int(round(x2))), "y_max": min(h, int(round(y2)))}
            for (x1, y1, x2, y2), c, k in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist(), r.boxes.cls.tolist())
        ]


def desenhar(frame, caixas):
    """Desenha as caixas no frame (altera e devolve o próprio frame). Usado no vídeo e nos frames anotados."""
    esp = max(2, round(min(frame.shape[:2]) / 360))
    escala = max(0.5, min(frame.shape[:2]) / 900)
    for b in caixas:
        x1, y1, x2, y2 = b["x_min"], b["y_min"], b["x_max"], b["y_max"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), VERDE, esp)
        rotulo = f'{b["classe"]} {b["confianca"]:.2f}'
        (tw, th), base = cv2.getTextSize(rotulo, cv2.FONT_HERSHEY_SIMPLEX, escala, max(1, esp // 2))
        topo = y1 - th - base - 4 if y1 - th - base - 4 >= 0 else y1
        cv2.rectangle(frame, (x1, topo), (x1 + tw + 6, topo + th + base + 4), VERDE, -1)
        cv2.putText(frame, rotulo, (x1 + 3, topo + th + 2), cv2.FONT_HERSHEY_SIMPLEX, escala,
                    (0, 0, 0), max(1, esp // 2), cv2.LINE_AA)
    return frame
