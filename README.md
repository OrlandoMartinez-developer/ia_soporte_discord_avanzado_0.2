
# IA de Soporte Técnico Inteligente (Discord + RAG + OCR + Asana)

Este bot conecta Discord con una IA local (via llama.cpp), soporte técnico por RAG, reconocimiento de texto en imágenes (OCR), y escalamiento automático a Asana.

---

## 🔧 CONFIGURACIONES MANUALES NECESARIAS:

1. **Discord Bot Token**
   - Archivo: `bot.py`
   - Línea: `TOKEN = "TU_TOKEN_DISCORD"`

2. **Asana**
   - Archivo: `config.py`
   - Reemplaza:
     - `ASANA_TOKEN = "tu_token_personal"`
     - `PROYECTO_ID = "ID_DEL_PROYECTO"`
     - IDs de los técnicos en la lista `TECNICOS`

3. **Modelo llama.cpp**
   - Archivo: `models/mistral.gguf` (coloca aquí tu modelo `.gguf`)
   - Descárgalo desde: https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF

4. **Documentación**
   - Carpeta: `docs/`
   - Agrega aquí archivos `.txt` que representen tus manuales o base de conocimiento.

---

## ▶️ Instrucciones

### Crear entorno e instalar dependencias

```bash
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install -r requirements.txt
```

### Indexar documentos

```bash
python index_docs.py
```

### Ejecutar el bot

```bash
python bot.py
```
