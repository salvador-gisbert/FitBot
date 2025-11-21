import os
import asyncio
import asyncpg
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, Application
from PIL import Image
import numpy as np
from io import BytesIO
from ultralytics import YOLO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
POINT_CLASS = 10

DB_USER = os.getenv("DB_USER")
if not DB_USER:
    raise ValueError("❌ ¡Falta la variable DB_USER en el archivo .env!")
# Bueno: Si no hay contraseña en .env, devuelve None (vacío) o falla.

DB_PASSWORD = os.getenv("DB_PASSWORD") 
# O mejor aún, forzar el error si falta:
if not DB_PASSWORD:
    raise ValueError("❌ ¡Falta la variable DB_PASSWORD en el archivo .env!")

DB_NAME = os.getenv("DB_NAME")
if not DB_USER:
    raise ValueError("❌ ¡Falta la variable DB_NAME en el archivo .env!")

DB_HOST = os.getenv("DB_HOST")
if not DB_HOST:
    raise ValueError("❌ ¡Falta la variable DB_HOST en el archivo .env!")

DB_PORT = os.getenv("DB_PORT")
if not DB_PORT:
    raise ValueError("❌ ¡Falta la variable DB_PORT en el archivo .env!")

DB_CONFIG = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "host": DB_HOST,
    "port": DB_PORT
}

# Cargamos el modelo fuera para que esté listo
model = YOLO("runs/detect/yolov8_custom/weights/best.pt")

db_pool = None
ultimo_peso = None

async def init_db():
    global db_pool
    print("🔌 Conectando a la base de datos...")
    try:
        db_pool = await asyncpg.create_pool(**DB_CONFIG)
        await db_pool.execute("""
            CREATE TABLE IF NOT EXISTS pesos (
                id SERIAL PRIMARY KEY,
                peso TEXT NOT NULL,
                confirmado BOOLEAN DEFAULT NULL,
                creado TIMESTAMP DEFAULT NOW()
            )
        """)
        print("✅ Base de datos conectada y tabla verificada.")
    except Exception as e:
        print(f"❌ Error conectando a BBDD: {e}")

# --- NUEVA FUNCIÓN: Se ejecuta justo antes de iniciar el bot ---
async def post_init(application: Application):
    await init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu bot funcionando correctamente. Envíame un mensaje o una imagen.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ultimo_peso
    text = update.message.text.strip().lower()

    if ultimo_peso and text in ["si", "sí", "s"]:
        if db_pool:
            await db_pool.execute("INSERT INTO pesos(peso, confirmado) VALUES($1, TRUE)", ultimo_peso)
            await update.message.reply_text(f"✅ Peso {ultimo_peso} guardado correctamente.")
        else:
            await update.message.reply_text("⚠️ Error: No hay conexión a la base de datos.")
        ultimo_peso = None
    elif ultimo_peso and text in ["no", "n"]:
        if db_pool:
            await db_pool.execute("INSERT INTO pesos(peso, confirmado) VALUES($1, FALSE)", ultimo_peso)
            await update.message.reply_text(f"❌ Peso {ultimo_peso} descartado.")
        else:
             await update.message.reply_text("⚠️ Error: No hay conexión a la base de datos.")
        ultimo_peso = None
    else:
        await update.message.reply_text(f"Recibí tu mensaje: {update.message.text}")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ultimo_peso
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    image = Image.open(BytesIO(photo_bytes))
    img_np = np.array(image)

    results = model(img_np)
    if len(results) > 0:
        for r in results:
            boxes = r.boxes
            filtered = []

            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                if conf < 0.6:
                    continue
                x1, y1, x2, y2 = box.xyxy[0]
                xc = float((x1 + x2) / 2)
                filtered.append((xc, cls, conf, (x1, y1, x2, y2)))

            if not filtered:
                await update.message.reply_text("Detecté objetos pero con baja confianza.")
                return

            filtered = sorted(filtered, key=lambda x: x[0])
            final_symbols = []
            for _, cls, conf, _ in filtered:
                final_symbols.append("." if cls == POINT_CLASS else str(cls))

            numero_final = "".join(final_symbols)
            # Ajuste simple para formato XX.XX (puedes mejorarlo según tu lógica)
            if len(numero_final) > 2 and "." not in numero_final:
                 numero_final = f"{numero_final[0:2]}.{numero_final[2:]}"
            
            ultimo_peso = numero_final
            mensaje = f"Tu peso es {numero_final}? (Responde SI / NO)"
            await update.message.reply_text(mensaje)
            return
    else:
        await update.message.reply_text("No pude detectar ningún objeto en la imagen.")

async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_pool:
         await update.message.reply_text("Error de conexión BBDD.")
         return

    # Obtenemos los últimos 10 registros
    rows = await db_pool.fetch("SELECT peso, confirmado, creado FROM pesos ORDER BY id DESC LIMIT 10")

    if not rows:
        await update.message.reply_text("📭 La base de datos está vacía.")
        return

    mensaje = "📋 **Últimos 10 pesajes:**\n\n"
    for row in rows:
        icono = "✅" if row['confirmado'] else "❌"
        fecha = row['creado'].strftime("%d/%m %H:%M")
        mensaje += f"{icono} {row['peso']} kg ({fecha})\n"

    await update.message.reply_text(mensaje, parse_mode="Markdown")

async def grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db_pool:
        await update.message.reply_text("Error de conexión BBDD.")
        return

    # 1. Consultar datos (Solo confirmados = TRUE, último año)
    query = """
        SELECT peso, creado 
        FROM pesos 
        WHERE confirmado = TRUE 
        AND creado > NOW() - INTERVAL '1 year'
        ORDER BY creado ASC
    """
    rows = await db_pool.fetch(query)

    if not rows:
        await update.message.reply_text("📉 No hay suficientes datos confirmados para generar una gráfica.")
        return

    # 2. Procesar datos
    fechas = [row['creado'] for row in rows]
    try:
        # Convertimos texto a float. Si falla alguno, lo saltamos
        pesos = [float(row['peso']) for row in rows]
    except ValueError:
        await update.message.reply_text("⚠️ Error: Hay datos no numéricos en la base de datos que impiden generar la gráfica.")
        return

    # 3. Crear Gráfico con Matplotlib
    plt.figure(figsize=(10, 6)) # Tamaño de la imagen
    plt.plot(fechas, pesos, marker='o', linestyle='-', color='#2ecc71', linewidth=2, markersize=6)
    
    # Títulos y etiquetas
    plt.title('Evolución de Peso (Último Año)')
    plt.xlabel('Fecha')
    plt.ylabel('Peso (kg)')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Formato de fechas en el eje X (Día/Mes)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate() # Rotar fechas para que no se solapen

    # 4. Guardar gráfico en memoria (buffer)
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close() # Cerrar para liberar memoria

    # 5. Enviar foto
    await update.message.reply_photo(photo=buf, caption="📊 Aquí tienes tu progreso.")

def main():
    # --- CAMBIO IMPORTANTE ---
    # Usamos post_init para la DB y quitamos asyncio.run()
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("historial", historial))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(CommandHandler("grafico", grafico))
    
    print("Bot corriendo…")
    # run_polling gestiona su propio bucle, por eso main() ya no es async
    app.run_polling()

if __name__ == "__main__":
    main()
