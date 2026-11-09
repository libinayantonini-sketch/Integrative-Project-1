"""Fila de processamento: os vídeos são analisados um de cada vez, numa thread separada,
para que o envio (POST /api/analises) responda na hora."""
import logging
import queue
import threading

from visao import pipeline

log = logging.getLogger(__name__)


class FilaProcessamento:
    def __init__(self, detector):
        self.detector = detector
        self._fila = queue.Queue()
        self._thread = threading.Thread(target=self._trabalhar, name="processamento", daemon=True)
        self._thread.start()

    def adicionar(self, id_proc):
        self._fila.put(id_proc)

    def _trabalhar(self):
        while True:
            id_proc = self._fila.get()
            try:
                pipeline.processar(id_proc, self.detector)
            except Exception:
                log.exception("Erro inesperado no processamento %s", id_proc)
            finally:
                self._fila.task_done()
