# Homelab Scanner

Herramienta de línea de comandos en Python que escanea una red controlada (Homelab), detecta puertos abiertos y servicios activos, y genera un reporte en PDF — construida como proyecto de aprendizaje práctico en ciberseguridad.

## ⚠️ Aviso legal y ético

Esta herramienta está diseñada **exclusivamente** para uso en entornos controlados y de laboratorio (máquinas virtuales propias, redes aisladas) o redes sobre las que se cuenta con autorización explícita. Escanear redes o sistemas de terceros sin autorización es ilegal en la mayoría de jurisdicciones. El autor no se hace responsable del uso indebido de este software.

## Qué hace

- Recibe una IP o rango de red (notación CIDR) por línea de comandos.
- Escanea los puertos más comunes de cada host detectado.
- Identifica el servicio activo en cada puerto abierto.
- Genera un reporte en PDF con los resultados, incluyendo metadatos de trazabilidad (ID de escaneo, fecha, rango analizado).

## Por qué existe este proyecto

Este es el primer proyecto práctico de una ruta de aprendizaje autodidacta en ciberseguridad, construido siguiendo un proceso real de desarrollo de software: especificación de requisitos (SRS) antes de escribir código, arquitectura modular, y pruebas contra un entorno vulnerable real (Metasploitable2).

La especificación completa de requisitos está disponible en [`docs/SRS.md`](docs/SRS.md).

## Stack técnico

- **Python 3** (sin frameworks externos para la lógica de escaneo)
- **Nmap**, invocado vía `subprocess` y parseado desde su salida XML
- **ReportLab** para la generación de PDF

## Instalación

```bash
git clone <url-del-repositorio>
cd homelab-scanner
pip install -r requirements.txt --break-system-packages
```

Requiere tener [Nmap](https://nmap.org/) instalado en el sistema (viene preinstalado en Kali Linux).

## Uso

```bash
python3 -m scanner.cli <IP o rango CIDR> [--timeout SEGUNDOS] [--output archivo.pdf] [--full] [--excel]
```

| Opción | Qué hace |
| --- | --- |
| `--timeout SEGUNDOS` | Tiempo máximo antes de cancelar el escaneo (default: 300) |
| `--output archivo.pdf` | Nombre del archivo PDF a generar (default: `reporte_scan.pdf`) |
| `--full` | Escanea los 65535 puertos en vez del modo rápido (puertos comunes) |
| `--excel` | Genera también un reporte en Excel (.xlsx), además del PDF |

Ejemplos:

```bash
python3 -m scanner.cli 192.168.56.0/24
python3 -m scanner.cli 192.168.56.10 --full --excel
```

## Estructura del proyecto

```
homelab-scanner/
├── scanner/
│   ├── cli.py          # Interfaz de línea de comandos
│   ├── scan_engine.py  # Motor de escaneo (Nmap vía subprocess)
│   ├── models.py        # Estructura de datos interna
│   ├── report.py        # Generación del reporte PDF
│   └── excel_export.py  # Generación del reporte Excel
├── docs/
│   └── SRS.md           # Especificación de requisitos
└── requirements.txt
```

## Entorno de pruebas

Desarrollado y probado en una red interna aislada de VirtualBox, con Kali Linux como máquina atacante y Metasploitable2 como objetivo vulnerable.

## Roadmap (mejoras futuras)

- [x] Modo de escaneo completo (65535 puertos) además del modo rápido actual
- [x] Exportación de resultados también a Excel (.xlsx)
- [ ] Soporte para IPv6
