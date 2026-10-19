"""
models.py
---------
Define la estructura de datos interna del escaneo (RF-7) y garantiza
que cada resultado quede vinculado a un identificador único de
ejecución, el Scan ID (RF-10, RNF-5).

Nada de este archivo ejecuta un escaneo real -- solo define "la forma"
que deben tener los datos. Esto es intencional: separamos "qué forma
tienen los datos" de "cómo se obtienen" (eso vive en scan_engine.py)
y de "cómo se muestran" (eso vive en report.py).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class PortResult:
    """
    Resultado de un único puerto analizado en un host.

    RF-4: guarda el servicio detectado.
    RF-6: si no se pudo identificar el servicio, 'service' queda
          como "no identificado" en vez de lanzar una excepción
          que detenga todo el escaneo.
    """
    port: int
    state: str  # "open", "closed", "filtered"
    service: str = "no identificado"


@dataclass
class HostResult:
    """
    Resultado de un host completo dentro del escaneo.
    Agrupa todos los PortResult encontrados en esa IP.
    """
    ip: str
    ports: list[PortResult] = field(default_factory=list)


@dataclass
class ScanSession:
    """
    Representa UNA ejecución completa del escaneo.

    Esta es la pieza central de RNF-5 (integridad/trazabilidad):
    todo lo que se descubre en esta ejecución -- cada host, cada
    puerto -- vive DENTRO de este objeto, por lo tanto queda
    vinculado automáticamente al mismo scan_id. No existe forma de
    que un resultado "se mezcle" con el de otra ejecución, porque
    cada ejecución crea su propio ScanSession.
    """
    target_range: str                      # RF-1: rango/IP solicitado
    scan_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )                                       # RF-10: identificador único
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )                                       # RF-10: fecha/hora en ISO 8601
    hosts: list[HostResult] = field(default_factory=list)

    def add_host(self, host: HostResult) -> None:
        """Agrega un host ya escaneado a esta sesión."""
        self.hosts.append(host)

    @property
    def host_count(self) -> int:
        """RF-10: cantidad de hosts detectados, para el reporte."""
        return len(self.hosts)
