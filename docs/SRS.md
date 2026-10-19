# Especificación de Requisitos de Software (SRS)

## Sistema de Escaneo de Red — Proyecto Homelab (Fase 1)

*Basado en los principios de ISO/IEC/IEEE 29148*

---

## 1. Introducción

### 1.1 Propósito del documento

Este documento especifica los requisitos de un sistema de escaneo y reporte de seguridad para una red de laboratorio controlada (Homelab). Su finalidad es doble: (1) servir como guía técnica estructurada durante el desarrollo del proyecto, y (2) funcionar como pieza de portafolio público que demuestre la capacidad de documentar, diseñar y construir una herramienta de ciberseguridad siguiendo prácticas profesionales.

### 1.2 Audiencia

Este documento está dirigido a:

- (a) El propio autor, como guía de desarrollo.
- (b) Reclutadores, clientes potenciales o colegas del área de ciberseguridad que revisen el portafolio.
- (c) Cualquier persona interesada en aprender sobre el proceso de construcción de herramientas de seguridad desde cero.

### 1.3 Definiciones y acrónimos

| Término | Definición |
| --- | --- |
| **Homelab** | Entorno de red virtualizado y aislado, ejecutado localmente mediante software de virtualización, utilizado exclusivamente con fines de aprendizaje y pruebas controladas. |
| **Host** | Dispositivo o máquina (física o virtual) identificable dentro de una red mediante una dirección IP. |
| **IP (dirección IP)** | Identificador numérico único que permite localizar y comunicar un host dentro de una red. |
| **Escaneo de puertos** | Proceso mediante el cual se identifican los puertos de red abiertos, cerrados o filtrados en un host, con el fin de determinar qué servicios se encuentran activos. |

---

## 2. Descripción General del Sistema

### 2.1 Perspectiva del producto

El sistema es una herramienta independiente, pero diseñada con un enfoque modular que permita reutilizar su motor de escaneo en proyectos futuros de ciberseguridad. Es el primer componente de un portafolio más amplio de herramientas desarrolladas en un entorno de laboratorio controlado (Homelab).

### 2.2 Funciones del producto

- Escanear un rango de direcciones IP dentro de una red controlada.
- Detectar puertos abiertos y servicios activos en cada host.
- Generar un reporte legible con los resultados del escaneo.

### 2.3 Características del usuario

El sistema está diseñado para ser operado tanto por el propio desarrollador (con conocimientos técnicos) como por usuarios con poca o nula experiencia en ciberseguridad, mediante una ejecución simple y mensajes de salida claros.

---

## 3. Requisitos Funcionales

### 3.1 Escaneo de red

- **RF-1**: El sistema debe aceptar como entrada, por línea de comandos, una dirección IP individual o un rango de IPs en notación CIDR (ej. 192.168.56.0/24).
- **RF-2**: El sistema debe escanear, para cada host detectado en el rango especificado, un conjunto predefinido de puertos comunes (ej. los definidos por defecto en la herramienta de escaneo utilizada).
- **RF-3** *(mejora futura — Should have)*: El sistema podrá, en una versión posterior, permitir al usuario elegir entre un modo de escaneo rápido (puertos comunes) y un modo completo (65535 puertos).

### 3.2 Detección de servicios activos

- **RF-4**: El sistema debe identificar el servicio asociado a cada puerto abierto detectado (ej. HTTP, SSH, FTP), basándose en la información proporcionada por la herramienta de escaneo subyacente.
- **RF-5** *(mejora futura — Should have)*: El sistema podrá, en una versión posterior, reportar también la versión específica del servicio detectado cuando esté disponible.
- **RF-6**: Si el sistema no logra identificar el servicio asociado a un puerto abierto, debe registrarlo en el reporte como "servicio no identificado" y continuar el proceso de escaneo sin detenerse.

### 3.3 Generación de reporte

- **RF-7**: El sistema debe organizar los resultados del escaneo (host, puertos abiertos, servicios detectados) en una estructura de datos interna antes de generar cualquier salida.
- **RF-8**: El sistema debe exportar los resultados a un archivo PDF, legible por cualquier persona sin necesidad de herramientas técnicas adicionales.
- **RF-9** *(mejora futura — Should have)*: El sistema podrá, en una versión posterior, exportar también los resultados a formato Excel (.xlsx), reutilizando la misma estructura de datos del RF-7.
- **RF-10**: El reporte generado debe incluir, como mínimo, los siguientes metadatos: identificador único de la ejecución (Scan ID), fecha y hora de inicio del escaneo (timestamp), rango de IPs analizado, y cantidad de hosts detectados.

---

## 4. Requisitos No Funcionales

- **RNF-1 (Rendimiento)**: El sistema debe completar el escaneo de una red de hasta 10 hosts en un tiempo no mayor a 5 minutos, en condiciones normales de red local.
- **RNF-2 (Portabilidad)**: El sistema debe ejecutarse en cualquier distribución Linux con Python 3.8 o superior instalado, sin requerir dependencias adicionales fuera de las especificadas en su documentación.
- **RNF-3 (Usabilidad)**: El sistema debe poder instalarse y ejecutarse siguiendo no más de 5 pasos documentados, sin requerir conocimientos avanzados de programación.
- **RNF-4 (Contención / Seguridad del sistema)**: El sistema no debe, bajo ninguna circunstancia, escanear direcciones IP fuera del rango explícitamente especificado por el usuario en el momento de la ejecución.
- **RNF-5 (Integridad de datos / Trazabilidad interna)**: Todo resultado individual generado durante una ejecución (por host, por puerto, por servicio) debe estar vinculado internamente al identificador único (Scan ID) de esa ejecución, garantizando que no exista ambigüedad entre resultados de distintas ejecuciones.

---

## 5. Supuestos y Restricciones

### 5.1 Supuestos

- **S-1**: Se asume que el usuario puede instalar Python 3.8 o superior en su entorno.
- **S-2**: Se asume que el usuario cuenta con un software de virtualización (ej. VirtualBox) y una distribución Linux compatible para ejecutar el sistema.
- **S-3**: Se asume que el usuario tiene autorización explícita para escanear la red objetivo.

### 5.2 Restricciones

- **R-1**: El sistema soporta únicamente direcciones IPv4; el soporte para IPv6 queda fuera del alcance de esta versión.
- **R-2**: El sistema está diseñado para operar exclusivamente en redes controladas/de laboratorio, no en redes de producción o de terceros sin autorización.
