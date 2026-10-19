"""
scan_engine.py
---------------
Motor de escaneo del proyecto Homelab.

Este módulo es el "corazón técnico" del sistema: se encarga de
invocar a Nmap como proceso externo, leer su resultado y convertirlo
en los objetos definidos en models.py (ScanSession, HostResult,
PortResult).

¿POR QUÉ subprocess en vez de una librería como python-nmap?
--------------------------------------------------------------
Nmap es, en sí mismo, un programa de línea de comandos escrito en
C/C++. Cuando Python "llama" a Nmap, en realidad no está ejecutando
código de Nmap dentro de Python -- está abriendo un proceso del
sistema operativo totalmente aparte (como si tú mismo escribieras
"nmap ..." en la terminal) y luego leyendo lo que ese proceso
devuelve. Esto es exactamente lo que hace el módulo `subprocess` de
Python: lanzar procesos externos y capturar su salida.

Le pedimos a Nmap que entregue su resultado en formato XML
(`-oX -`, donde el "-" final significa "imprime el XML en la
salida estándar en vez de guardarlo en un archivo"). XML es un
formato estructurado y predecible, mucho más fácil y seguro de leer
por un programa que el texto "bonito" que Nmap muestra normalmente
en pantalla.

Flujo completo de este archivo:
    1. validar la entrada del usuario            -> validate_target()
    2. ejecutar Nmap como proceso externo          -> run_nmap_scan()
    3. convertir el XML crudo en nuestros modelos  -> parse_nmap_xml()
    4. orquestar los tres pasos anteriores         -> scan()
"""

import ipaddress
import subprocess
import xml.etree.ElementTree as ET

from scanner.models import HostResult, PortResult, ScanSession


# Tiempo máximo (en segundos) que dejamos correr a Nmap antes de
# cancelarlo. Esto conecta directamente con RNF-1 (rendimiento): si
# el escaneo se queda "colgado" por algún motivo, no dejamos que el
# programa se congele para siempre.
DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutos


class InvalidTargetError(Exception):
    """
    Se lanza cuando el usuario ingresa algo que no es una IP o rango
    IPv4 válido. Tener una excepción propia (en vez de usar errores
    genéricos de Python) hace que, más adelante, cli.py pueda
    mostrar un mensaje claro al usuario en vez de un error técnico
    confuso.
    """
    pass


def validate_target(target_range: str) -> str:
    """
    Valida que lo que escribió el usuario sea una IP o un rango
    IPv4 válido (RF-1, R-1: solo IPv4, sin soporte para IPv6).

    Usamos el módulo estándar `ipaddress` de Python, que ya sabe
    reconocer tanto una IP suelta ("192.168.56.10") como un rango
    en notación CIDR ("192.168.56.0/24") -- no reinventamos esa
    lógica a mano, porque validar IPs manualmente con expresiones
    regulares es una fuente clásica de errores.

    Devuelve el mismo target_range si es válido, o lanza
    InvalidTargetError si no lo es.
    """
    try:
        red = ipaddress.ip_network(target_range, strict=False)
    except ValueError:
        raise InvalidTargetError(
            f"'{target_range}' no es una IP ni un rango válido."
        )

    if red.version != 4:
        # R-1: el sistema, en esta versión, NO soporta IPv6.
        raise InvalidTargetError(
            "Solo se admiten direcciones IPv4 en esta versión del sistema."
        )

    return target_range


def run_nmap_scan(
    target_range: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """
    Ejecuta Nmap como proceso externo y devuelve su salida en XML
    (como texto, sin procesar todavía).

    Parámetros del comando que usamos:
        -sV   -> detección de servicio/versión (RF-4)
        -Pn   -> omite la fase de "host discovery" (ping) y escanea
                 los puertos directamente, asumiendo que el host
                 está activo. CASO LÍMITE que motivó esto: durante
                 las pruebas de este proyecto, un host real y
                 accesible (Metasploitable2) fue reportado sin
                 ningún puerto porque no respondió al ping previo
                 de Nmap -- un comportamiento normal en muchas redes
                 de laboratorio/VMs, donde el ICMP puede estar
                 bloqueado o no configurado aunque el host sí esté
                 arriba y sus servicios sí sean alcanzables. Sin
                 -Pn, ese escenario produce un falso negativo (el
                 sistema reporta "sin resultados" cuando en realidad
                 el host sí tenía puertos abiertos).
        -oX - -> escribe el resultado en XML hacia la salida
                 estándar en vez de un archivo
        (sin -p) -> al no especificar puertos, Nmap escanea sus
                 ~1000 puertos "top" más comunes por defecto, NO
                 los 65535. Esto es exactamente lo que pide RF-2
                 para la V1 del sistema.

    Nota sobre un host genuinamente apagado/inexistente: con -Pn,
    Nmap igual intenta escanear sus puertos -- el resultado, en ese
    caso, es que todos los puertos aparecen como "filtered" (no se
    pudo determinar su estado porque no hubo respuesta de ningún
    tipo). El sistema no trata esto como un error: simplemente lo
    refleja tal cual en el reporte (RF-6: no se detiene el proceso).

    RNF-4 (contención): el único objetivo que se escanea es,
    literalmente, el string `target_range` que el usuario mandó por
    la línea de comandos -- nunca se agrega, infiere, ni expande
    ningún otro rango por fuera de ese valor.
    """
    comando = ["nmap", "-sV", "-Pn", "-oX", "-", target_range]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,  # captura stdout y stderr
            text=True,            # devuelve strings, no bytes
            timeout=timeout,      # RNF-1: evita que se quede colgado
            check=True,           # lanza excepción si Nmap devuelve error
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError(
            f"El escaneo de '{target_range}' superó el tiempo límite "
            f"de {timeout} segundos."
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Nmap terminó con un error al escanear '{target_range}': "
            f"{error.stderr}"
        )
    except FileNotFoundError:
        raise RuntimeError(
            "No se encontró el ejecutable 'nmap'. "
            "¿Está instalado en este sistema? (sudo apt install nmap)"
        )

    return resultado.stdout


def parse_nmap_xml(xml_data: str, target_range: str) -> ScanSession:
    """
    Convierte el XML crudo que devuelve Nmap en un ScanSession
    (RF-7: estructura de datos interna) con sus HostResult y
    PortResult correspondientes.

    La estructura típica del XML de Nmap es, simplificada:

        <nmaprun>
            <host>
                <address addr="192.168.56.20" .../>
                <ports>
                    <port portid="22" protocol="tcp">
                        <state state="open" .../>
                        <service name="ssh" .../>
                    </port>
                    ...
                </ports>
            </host>
            ...
        </nmaprun>

    Recorremos ese árbol con xml.etree.ElementTree, la librería
    estándar de Python para leer XML (no requiere instalar nada
    adicional).
    """
    # Creamos la sesión primero: esto genera automáticamente el
    # Scan ID y el timestamp (ver models.py) ANTES de leer ningún
    # resultado, para que absolutamente todo lo que agreguemos a
    # partir de aquí quede vinculado a esta misma ejecución (RNF-5).
    sesion = ScanSession(target_range=target_range)

    raiz = ET.fromstring(xml_data)

    for host_xml in raiz.findall("host"):
        direccion_el = host_xml.find("address")
        if direccion_el is None:
            # Un host sin dirección es un dato incompleto e inusual;
            # lo saltamos en vez de detener TODO el escaneo por un
            # solo host raro (misma filosofía "fail gracefully"
            # que ya definimos para RF-6).
            continue

        host_resultado = HostResult(ip=direccion_el.get("addr"))

        puertos_el = host_xml.find("ports")
        if puertos_el is not None:
            for puerto_xml in puertos_el.findall("port"):
                numero_puerto = int(puerto_xml.get("portid"))

                estado_el = puerto_xml.find("state")
                estado = estado_el.get("state") if estado_el is not None else "desconocido"

                # RF-6: si Nmap no pudo identificar el servicio,
                # usamos el valor por defecto ya definido en
                # PortResult ("no identificado") en vez de fallar.
                servicio_el = puerto_xml.find("service")
                if servicio_el is not None and servicio_el.get("name"):
                    nombre_servicio = servicio_el.get("name")
                else:
                    nombre_servicio = "no identificado"

                host_resultado.ports.append(
                    PortResult(
                        port=numero_puerto,
                        state=estado,
                        service=nombre_servicio,
                    )
                )

        sesion.add_host(host_resultado)

    return sesion


def scan(
    target_range: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> ScanSession:
    """
    Función principal del módulo: orquesta validación + ejecución +
    parseo, y devuelve un ScanSession listo para pasar a report.py.

    Esta es la ÚNICA función que el resto del programa (cli.py)
    necesita llamar -- no necesita saber nada sobre subprocess ni
    sobre XML. Eso es "encapsulamiento": escondemos el detalle
    técnico detrás de una función simple de usar.
    """
    target_range = validate_target(target_range)
    xml_crudo = run_nmap_scan(target_range, timeout=timeout)
    return parse_nmap_xml(xml_crudo, target_range)
