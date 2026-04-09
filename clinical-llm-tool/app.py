import os
import json
import requests
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from werkzeug.utils import secure_filename
import PyPDF2
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'

OLLAMA_BASE_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text.strip())
    return '\n\n'.join(text_parts)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/models')
def list_models():
    try:
        resp = requests.get(f'{OLLAMA_BASE_URL}/api/tags', timeout=5)
        resp.raise_for_status()
        models = [m['name'] for m in resp.json().get('models', [])]
        return jsonify({'models': models})
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to Ollama. Is it running?'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body'}), 400

    model = data.get('model', 'llama3')
    messages = data.get('messages', [])
    stream = data.get('stream', False)

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    payload = {
        'model': model,
        'messages': messages,
        'stream': stream,
    }

    if stream:
        def generate():
            try:
                with requests.post(
                    f'{OLLAMA_BASE_URL}/api/chat',
                    json=payload,
                    stream=True,
                    timeout=120
                ) as r:
                    for line in r.iter_lines():
                        if line:
                            yield f"data: {line.decode('utf-8')}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
            }
        )

    try:
        resp = requests.post(
            f'{OLLAMA_BASE_URL}/api/chat',
            json=payload,
            timeout=120
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to Ollama. Is it running?'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Use PDF, TXT, or MD'}), 400

    filename = secure_filename(file.filename)
    file_bytes = file.read()
    ext = filename.rsplit('.', 1)[1].lower()

    if ext == 'pdf':
        try:
            text = extract_text_from_pdf(file_bytes)
        except Exception as e:
            return jsonify({'error': f'Failed to parse PDF: {str(e)}'}), 400
    else:
        try:
            text = file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            text = file_bytes.decode('latin-1')

    word_count = len(text.split())
    char_count = len(text)

    return jsonify({
        'filename': filename,
        'text': text,
        'word_count': word_count,
        'char_count': char_count,
    })


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print('Starting Clinical LLM Tool...')
    print(f'Ollama endpoint: {OLLAMA_BASE_URL}')
    print('Open http://localhost:5000 in your browser')
    app.run(host='0.0.0.0', port=5000, debug=True)
