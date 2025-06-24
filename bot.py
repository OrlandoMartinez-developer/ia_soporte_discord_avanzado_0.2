
import discord
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
import chromadb
import pytesseract
from PIL import Image
import requests
from io import BytesIO

from config import ASANA_TOKEN, PROYECTO_ID, TECNICOS, RECURSOS_EMPRESA

TOKEN = "TU_TOKEN_DISCORD"

llm = Llama(model_path="models/mistral.gguf", n_ctx=2048, n_threads=6)
embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma = chromadb.Client()
collection = chroma.get_or_create_collection("docs")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def es_problema_interno(texto):
    texto = texto.lower()
    for recurso in RECURSOS_EMPRESA:
        if recurso in texto:
            return True
    return False

def asignar_tecnico(categoria):
    for tecnico in TECNICOS:
        if categoria in tecnico["categorias"]:
            return tecnico["id"]
    return TECNICOS[0]["id"]

def crear_tarea_asana(titulo, descripcion, responsable_id):
    import requests
    headers = {
        "Authorization": f"Bearer {ASANA_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "data": {
            "name": titulo,
            "notes": descripcion,
            "assignee": responsable_id,
            "projects": [PROYECTO_ID]
        }
    }
    response = requests.post("https://app.asana.com/api/1.0/tasks", headers=headers, json=data)
    return response.status_code

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.attachments:
        for file in message.attachments:
            if file.content_type.startswith("image"):
                response = requests.get(file.url)
                img = Image.open(BytesIO(response.content))
                text = pytesseract.image_to_string(img)
                await message.channel.send(f"🖼️ Texto detectado: ```{text.strip()[:200]}...```")
                query = text
                break
    else:
        query = message.content

    query_embed = embedder.encode(query).tolist()
    result = collection.query(query_embeddings=[query_embed], n_results=1)
    contexto = result["documents"][0][0] if result["documents"] else "Sin contexto."

    prompt = f"""
Eres un asistente técnico para una empresa. Usa la información si es útil:
{contexto}

Pregunta: {query}
¿Este problema parece interno (relacionado a la empresa) o externo?
Respuesta:
"""

    output = llm(prompt=prompt, stop=["\n"], max_tokens=200)
    respuesta = output["choices"][0]["text"].strip()
    interno = es_problema_interno(query) or "sí" in respuesta.lower()

    if interno:
        responsable_id = asignar_tecnico("windows")  # puedes ajustar la categoría
        crear_tarea_asana(titulo=query[:50], descripcion=f"{query}

{contexto}", responsable_id=responsable_id)
        await message.channel.send("🛠️ No pude resolverlo. Se ha escalado a soporte técnico.")
    else:
        await message.channel.send(f"🤖 {respuesta}")
