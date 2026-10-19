"""
cli.py
------
Punto de entrada del programa: la interfaz de línea de comandos
(CLI, por sus siglas en inglés).

Este es el ÚNICO archivo que el usuario ejecuta directamente
(ej. "python -m scanner.cli 192.168.56.0/24"). Su única
responsabilidad es:

    1. Leer lo que el usuario escribió en la terminal (RF-1).
    2. Llamar al motor de escaneo (scan_engine.scan()).
    3. Mostrar errores de forma clara si algo sale mal, sin
       mostrarle al usuario un "traceback" técnico de Python que
       no va a entender (RNF-3: usabilidad).

cli.py NO sabe cómo funciona Nmap, ni cómo se arma el XML, ni cómo
se genera un PDF. Solo "orquesta" -- llama a las piezas que ya
construimos, en el orden correcto. Esta separación es la misma idea
de encapsulamiento que vimos en scan_engine.py, aplicada ahora al
programa completo.
"""

import argparse
import sys

from scanner.report import generate_pdf
from scanner.scan_engine import InvalidTargetError, scan


def construir_parser() -> argparse.ArgumentParser:
    """
    Define qué argumentos acepta el programa por línea de comandos.

    `argparse` es el módulo estándar de Python para esto -- además
    de leer los argumentos, genera automáticamente un mensaje de
    ayuda (`--help`) y valida que no falten argumentos obligatorios,
    sin que tengamos que programar eso a mano.
    """
    parser = argparse.ArgumentParser(
        prog="homelab-scanner",
        description=(
            "Escanea una red controlada (Homelab) y detecta puertos "
            "abiertos y servicios activos en cada host."
        ),
    )

    # RF-1: el usuario debe poder pasar una IP individual o un rango
    # en notación CIDR como argumento posicional (obligatorio).
    parser.add_argument(
        "target_range",
        help=(
            "IP individual (ej. 192.168.56.10) o rango CIDR "
            "(ej. 192.168.56.0/24) a escanear."
        ),
    )

    # Argumento opcional: permite ajustar el timeout sin tener que
    # tocar el código (RNF-1 configurable desde fuera).
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Tiempo máximo en segundos antes de cancelar el escaneo (default: 300).",
    )

    # RF-8: dónde guardar el PDF generado. Tiene un valor por
    # defecto para que el usuario no esté obligado a especificarlo.
    parser.add_argument(
        "--output",
        default="reporte_scan.pdf",
        help="Ruta del archivo PDF a generar (default: reporte_scan.pdf).",
    )

    return parser


def main() -> int:
    """
    Función principal. Devuelve un código de salida:
        0 -> todo salió bien
        1 -> hubo un error controlado (ej. IP inválida)

    Este patrón (devolver un código numérico) es el estándar en
    programas de línea de comandos: 0 significa éxito, cualquier
    otro número significa que algo falló. Otros programas que
    llamen al tuyo (ej. un script más grande) pueden revisar ese
    código para saber si continuar o no.
    """
    parser = construir_parser()
    argumentos = parser.parse_args()

    print(f"[*] Iniciando escaneo de: {argumentos.target_range}")
    print("[*] Esto puede tardar unos minutos dependiendo del rango...\n")

    try:
        sesion = scan(argumentos.target_range, timeout=argumentos.timeout)
    except InvalidTargetError as error:
        # Error esperado y controlado: el usuario escribió algo mal.
        # Mostramos un mensaje claro, NO el error técnico de Python.
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    except TimeoutError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    # Resumen rápido en pantalla. La generación del PDF (RF-8) la
    # conectamos en el siguiente paso, en report.py -- por ahora
    # mostramos los resultados para poder probar que el escaneo
    # funciona de punta a punta.
    print(f"[+] Scan ID: {sesion.scan_id}")
    print(f"[+] Fecha: {sesion.timestamp}")
    print(f"[+] Hosts detectados: {sesion.host_count}\n")

    for host in sesion.hosts:
        print(f"Host: {host.ip}")
        if not host.ports:
            print("    (sin puertos abiertos detectados)")
        for puerto in host.ports:
            print(f"    {puerto.port}/tcp  {puerto.state:<10} {puerto.service}")
        print()

    # RF-8: ahora que el escaneo terminó y ya se mostró en pantalla,
    # generamos también el PDF. Si por alguna razón esto falla (ej.
    # permisos de escritura en la carpeta), lo avisamos con claridad
    # pero NO perdemos el resultado que ya se mostró arriba -- el
    # escaneo en sí ya fue un éxito, el PDF es un paso adicional.
    try:
        ruta_generada = generate_pdf(sesion, output_path=argumentos.output)
        print(f"[+] Reporte PDF generado en: {ruta_generada}")
    except Exception as error:
        print(f"[ERROR] No se pudo generar el PDF: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    # Esto permite correr el archivo directamente con
    # "python -m scanner.cli ..." -- es el patrón estándar de
    # Python para distinguir "este archivo se ejecutó directamente"
    # de "este archivo fue importado desde otro lugar".
    sys.exit(main())
