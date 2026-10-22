import os
import time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from google import genai
from pypdf import PdfReader

app = Flask(__name__)
CORS(app)

# 🔑 Yahan apni AIzaSy... wali asli API key paste karein
MY_API_KEY =os.environ.get("GEMINI_API_KEY") 
# Client initialization
client = genai.Client(api_key=MY_API_KEY)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def home():
  return send_from_directory('.', 'index.html')


@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
  if 'file' not in request.files:
    return jsonify({'error': 'No file uploaded'}), 400

  file = request.files['file']
  if file.filename == '':
    return jsonify({'error': 'No selected file'}), 400

  if file and file.filename.endswith('.pdf'):
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    reader = PdfReader(filepath)
    extracted_text = ''
    for page in reader.pages:
      text = page.extract_text()
      if text:
        extracted_text += text + '\n'

    with open('temp_text.txt', 'w', encoding='utf-8') as f:
      f.write(extracted_text)

    return jsonify({
        'message': 'PDF processed successfully!',
        'filename': file.filename,
        'total_pages': len(reader.pages),
        'extracted_text_preview': extracted_text[:300] + '...',
    })


@app.route('/summarize-pdf', methods=['GET'])
def summarize_pdf():
  if not os.path.exists('temp_text.txt'):
    return jsonify({'error': 'No PDF processed yet.'}), 400

  with open('temp_text.txt', 'r', encoding='utf-8') as f:
    text = f.read()

  sample_text = text[:4000]
  prompt = (
      'You are an expert AI Study Assistant. Summarize the following study'
      ' notes clearly in simple bullet points with key concepts and important'
      f' topics for exam preparation:\n\n{sample_text}'
  )

  # Using gemini-1.5-flash as officially required by Google API
  model_name = 'gemini-1.5-flash'
  summary_text = None
  last_error = None

  for attempt in range(1, 4):
    print(f'-> Trying {model_name} (Attempt {attempt}/3)...')
    try:
      response = client.models.generate_content(
          model=model_name, contents=prompt
      )
      summary_text = response.text
      print('-> Successfully generated summary!')
      break
    except Exception as e:
      last_error = str(e)
      print(f'-> Attempt {attempt} failed: {last_error}')
      time.sleep(2)

  if not summary_text:
    summary_text = (
        'Error generating AI summary after multiple attempts. Details:'
        f' {last_error}'
    )

  return jsonify({'status': 'success', 'summary': summary_text})


if __name__ == '__main__':
  app.run(debug=True)
