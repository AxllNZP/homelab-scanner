"""
report.py
---------
Exporta un ScanSession (definido en models.py) a un archivo PDF
legible por cualquier persona, sin necesidad de herramientas
técnicas (RF-8).

Este archivo es la razón por la que separamos "los datos" (RF-7,
en models.py) de "cómo se muestran": recibe un ScanSession YA
armado -- no sabe nada de Nmap, ni de XML, ni de subprocess. Solo
sabe tomar esos datos y dibujarlos en un PDF. Si mañana quisieras
agregar un export a Excel (RF-9, la mejora futura que anotamos),
sería un archivo nuevo (ej. excel_export.py) que recibe el MISMO
ScanSession -- este archivo no tendría que cambiar en nada.

Usamos la librería `reportlab`, el estándar de facto en Python para
generar PDFs desde cero (no viene incluida con Python, por eso la
instalaste con pip).
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from scanner.models import ScanSession


def generate_pdf(sesion: ScanSession, output_path: str = "reporte_scan.pdf") -> str:
    """
    Genera un PDF a partir de un ScanSession y lo guarda en
    output_path. Devuelve la ruta del archivo generado.

    reportlab trabaja con el concepto de "documento + lista de
    elementos" (platypus): primero defines el documento (tamaño de
    página, márgenes), y luego le das una lista de "elementos" en
    el orden en que deben aparecer (un título, un párrafo, una
    tabla, etc.). reportlab se encarga de acomodarlos en las
    páginas automáticamente -- no tienes que calcular posiciones
    X/Y a mano.
    """
    documento = SimpleDocTemplate(output_path, pagesize=letter)
    estilos = getSampleStyleSheet()
    elementos = []  # aquí vamos a ir agregando todo lo que aparecerá en el PDF

    # --- Título ---
    elementos.append(Paragraph("Reporte de Escaneo de Red", estilos["Title"]))
    elementos.append(Spacer(1, 12))  # espacio en blanco (en puntos) entre elementos

    # --- Metadatos (RF-10) ---
    # Esta es la sección que garantiza que cualquiera que abra el
    # PDF sepa exactamente a qué ejecución corresponde, sin
    # ambigüedad (ver RNF-5).
    metadatos_texto = f"""
    <b>Scan ID:</b> {sesion.scan_id}<br/>
    <b>Fecha y hora:</b> {sesion.timestamp}<br/>
    <b>Rango analizado:</b> {sesion.target_range}<br/>
    <b>Hosts detectados:</b> {sesion.host_count}
    """
    elementos.append(Paragraph(metadatos_texto, estilos["Normal"]))
    elementos.append(Spacer(1, 20))

    # --- Resultados por host ---
    for host in sesion.hosts:
        elementos.append(Paragraph(f"Host: {host.ip}", estilos["Heading2"]))
        elementos.append(Spacer(1, 6))

        if not host.ports:
            elementos.append(
                Paragraph("Sin puertos abiertos detectados.", estilos["Normal"])
            )
            elementos.append(Spacer(1, 16))
            continue

        # Armamos la tabla: la primera fila son los encabezados,
        # el resto son los datos reales (uno por puerto).
        datos_tabla = [["Puerto", "Estado", "Servicio"]]
        for puerto in host.ports:
            datos_tabla.append([str(puerto.port), puerto.state, puerto.service])

        tabla = Table(datos_tabla, colWidths=[80, 100, 200])

        # TableStyle define la apariencia: qué celdas llevan color,
        # bordes, alineación, etc. Las coordenadas (0, 0) a (-1, -1)
        # significan "desde la primera celda hasta la última" --
        # es la forma de reportlab de decir "toda la tabla".
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2b2b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        elementos.append(tabla)
        elementos.append(Spacer(1, 16))

    # Esta es la línea que realmente "dibuja" todo y escribe el
    # archivo en disco -- todo lo anterior solo preparó la lista
    # de elementos en memoria.
    documento.build(elementos)

    return output_path
