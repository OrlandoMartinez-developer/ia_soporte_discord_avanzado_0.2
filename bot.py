import os
import discord
import asyncio
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
import chromadb
import pytesseract
from PIL import Image
import aiohttp
from io import BytesIO

from config import get_projects, get_users, oauth

# === TOKEN DISCORD ===
TOKEN = os.getenv("DISCORD_TOKEN") or "TU_TOKEN_DISCORD"

# === Carga diferida ===
llm = None
embedder = None

# === Chroma DB ===
chroma = chromadb.Client()
collection = chroma.get_or_create_collection("docs")

# === Discord ===
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# === Listas útiles ===
SALUDOS = ["hola", "buenos días", "buenas tardes", "buenas", "saludos", "qué tal", "hi", "hello"]
PALABRAS_PROBLEMA = ["error", "falla", "problema", "no funciona", "no carga", "pantalla", "crash", "bug", "congelado"]

# === Asana ===
def crear_tarea_asana(titulo, descripcion, responsable_id, proyecto_id):
    headers = {"Content-Type": "application/json"}
    data = {
        "data": {
            "name": titulo,
            "notes": descripcion,
            "assignee": responsable_id,
            "projects": [proyecto_id]
        }
    }
    response = oauth.post("https://app.asana.com/api/1.0/tasks", headers=headers, json=data)
    return response.status_code

# === IA: Obtener respuesta del modelo ===
async def generar_respuesta_llm(prompt):
    global llm
    if llm is None:
        print("🔄 Cargando modelo...")
        llm = Llama(
            model_path="models/phi-2.Q4_0.gguf",  # Puedes cambiar a Q2_K si es muy pesado
            n_ctx=512,
            n_threads=2
        )

    print("🧠 PROMPT:\n", prompt.strip())

    output = await asyncio.to_thread(
        lambda: llm(prompt=prompt, stop=["Usuario:", "</s>", "Asistente:"], max_tokens=150)
    )

    print("🧠 RAW OUTPUT:", output)

    respuesta = output["choices"][0].get("text", "").strip()
    if not respuesta:
        respuesta = "Lo siento, no entendí tu mensaje. ¿Puedes decirlo de otra forma?"
    return respuesta

# === OCR (Imagen a texto) ===
async def obtener_texto_imagen(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            img = Image.open(BytesIO(await resp.read()))
            return pytesseract.image_to_string(img)

# === Evento de conexión ===
@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")

# === Evento de mensaje ===
@client.event
async def on_message(message):
    if message.author.bot:
        return

    query = ""

    # 📷 Procesar imagen si hay adjunto
    if message.attachments:
        for file in message.attachments:
            if file.content_type and file.content_type.startswith("image"):
                texto = await obtener_texto_imagen(file.url)
                query = texto.strip()[:300]
                await message.channel.send(f"🖼️ Texto detectado: ```{query[:200]}...```")
                break

    if not query:
        query = message.content.strip()

    texto_lower = query.lower()

    # 🖐️ Saludo simple
    if any(saludo in texto_lower for saludo in SALUDOS):
        await message.channel.send("👋 ¡Hola! Soy tu asistente técnico. ¿En qué puedo ayudarte hoy?")
        return

    # === IA Embedding y contexto ===
    global embedder
    if embedder is None:
        embedder = SentenceTransformer("paraphrase-MiniLM-L3-v2")

    query_embed = embedder.encode(query).tolist()
    result = collection.query(query_embeddings=[query_embed], n_results=1)
    contexto = result["documents"][0][0] if result.get("documents") and result["documents"][0] else "Sin contexto."

    # === Si parece un problema técnico ===
    if any(palabra in texto_lower for palabra in PALABRAS_PROBLEMA):
        prompt = f"""
Eres un asistente técnico que ayuda a los usuarios con problemas tecnológicos. Usa esta información si es útil:
{contexto}

Usuario: {query}
¿Este problema parece interno (relacionado a la empresa) o externo?
Explica por qué brevemente.
Asistente:"""

        respuesta = await generar_respuesta_llm(prompt)

        if "sí" in respuesta.lower() or "interno" in respuesta.lower():
            users = get_users("workspace_id_placeholder")
            proyectos = get_projects("workspace_id_placeholder")

            responsable_id = users[0]["gid"] if users else None
            proyecto_id = proyectos[0]["gid"] if proyectos else None

            if responsable_id and proyecto_id:
                crear_tarea_asana(
                    titulo=query[:50],
                    descripcion=f"{query}\n\n{contexto}",
                    responsable_id=responsable_id,
                    proyecto_id=proyecto_id
                )
                await message.channel.send("🛠️ No pude resolverlo. Se ha escalado a soporte técnico.")
            else:
                await message.channel.send("⚠️ No se pudo asignar la tarea por falta de datos.")
        else:
            await message.channel.send(f"🤖 {respuesta}")
    else:
        # 💬 Conversación casual
        prompt = f"""
Eres un asistente amigable y conversacional. Responde de manera natural y clara.

Usuario: {query}
Asistente:"""

        respuesta = await generar_respuesta_llm(prompt)
        await message.channel.send(f"💬 {respuesta}")

# === Iniciar bot ===
if __name__ == '__main__':
    client.run(TOKEN)