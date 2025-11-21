# ⚖️ Báscula Bot AI: Auto-Tracking de Peso con Telegram & Computer Vision

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker&logoColor=white)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-purple)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql&logoColor=white)

> **"Estaba cansado de pagar suscripciones para trackear mi peso, así que automaticé mi báscula con Inteligencia Artificial."**

Este proyecto es un **Bot de Telegram** que permite llevar un registro automático de tu peso corporal simplemente enviando una foto de la pantalla de tu báscula. El sistema utiliza **Visión por Computador (YOLOv8)** para leer los dígitos, guarda los datos en **PostgreSQL** y genera gráficas de evolución bajo demanda.

---

## 📸 Funcionalidades

* **Detección Automática:** Envía una foto de la báscula y el bot detectará los dígitos usando un modelo YOLOv8 entrenado a medida.
* **Validación Humana:** El bot te preguntará si la lectura es correcta antes de guardar nada.
* **Persistencia de Datos:** Todos los registros se guardan de forma segura en una base de datos PostgreSQL.
* **Reportes Visuales:** Genera gráficos de evolución anual con `matplotlib` directamente en el chat.
* **Historial:** Consulta tus últimos pesajes rápidamente.
* **100% Dockerizado:** Despliegue sencillo y limpio con Docker Compose.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.13
* **Bot Framework:** `python-telegram-bot` (Async)
* **Computer Vision:** Ultralytics YOLOv8
* **Base de Datos:** PostgreSQL + `asyncpg`
* **Visualización:** Matplotlib
* **Infraestructura:** Docker & Docker Compose

---

## 📂 Estructura del Proyecto

```text
BASCULA/
├── BBDD/                   # Persistencia de datos de PostgreSQL (volumen)
├── LED.v6i.yolov8/         # Dataset de imágenes (si aplica)
├── runs/                   # Modelos YOLO entrenados (weights/best.pt)
├── bot.py                  # Lógica principal del Bot
├── docker-compose.yaml     # Orquestación de servicios
├── Dockerfile              # Construcción de la imagen del Bot
├── .env                    # Variables de entorno (Token, DB Creds)
└── requirements.txt        # Dependencias de Python
```

⚙️ Instalación y Despliegue
1. Requisitos Previos
Tener Docker y Docker Compose instalados.

Un Token de Telegram (consíguelo gratis en @BotFather).

2. Clonar el repositorio

```text
git clone [https://github.com/tu-usuario/bascula-bot-ai.git](https://github.com/tu-usuario/bascula-bot-ai.git)
cd bascula-bot-ai
```

3. Configurar Variables de Entorno
Crea un archivo .env en la raíz del proyecto y rellena tus datos:

4. Levantar el Proyecto
Ejecuta el siguiente comando para construir la imagen y levantar los contenedores:

```text
docker compose up --build -d
```
