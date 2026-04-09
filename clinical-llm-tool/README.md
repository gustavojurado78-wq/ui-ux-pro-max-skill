# Clinical LLM Tool

Interfaz web local para interactuar con modelos LLM (via Ollama) orientada a uso clínico.

## Requisitos

- Python 3.x con entorno virtual
- Ollama corriendo en `http://localhost:11434`
- GPU NVIDIA detectada (`nvidia-smi` OK)

## Instalación en WSL2

```bash
# 1. Clonar o copiar esta carpeta a tu WSL
cd ~
# Copia la carpeta clinical-llm-tool aquí

# 2. Crear entorno virtual (si no lo tienes)
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python app.py
```

Abre el navegador en: **http://localhost:5000**

## Estructura

```
clinical-llm-tool/
├── app.py              # Backend Flask
├── requirements.txt    # Dependencias Python
├── templates/
│   └── index.html      # Interfaz web
└── uploads/            # Carpeta temporal (auto-creada)
```

## Funcionalidades

- **Chat con LLM local** via Ollama (llama3, mistral, etc.)
- **Carga de PDF / TXT** — extrae texto automáticamente
- **Atajos clínicos**: formato SOAP, diagnóstico diferencial, extracción de medicamentos, etc.
- **Historial de conversación** con contexto del documento
- **100% local** — sin datos en la nube

## Solución de problemas

**Ollama no conecta:**
```bash
ollama serve   # asegúrate de que esté corriendo
ollama list    # lista modelos disponibles
ollama pull llama3   # descarga el modelo si no lo tienes
```

**Puerto 5000 ocupado:**
```bash
python app.py  # por defecto usa 5000
# o cambia el puerto en la última línea de app.py: port=5001
```
