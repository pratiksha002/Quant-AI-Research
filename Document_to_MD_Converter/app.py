import os
import uuid
import tempfile
import io
import zipfile
from flask import Flask, request, jsonify, render_template, send_file
from concurrent.futures import ProcessPoolExecutor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models import SessionLocal, BatchHistory, FileConversion, DATABASE_URL, Base, engine
from converter import DocumentConverter

load_dotenv()

app = Flask(__name__)

# Database Initialization
with app.app_context():
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")

executor = ProcessPoolExecutor(max_workers=os.cpu_count() or 4)

def process_file_task(file_record_id, db_url):
    worker_engine = create_engine(db_url)
    Session = sessionmaker(bind=worker_engine)
    session = Session()
    
    file_record = session.query(FileConversion).filter(FileConversion.id == file_record_id).first()
    if not file_record or not file_record.original_file_data:
        session.close()
        return
        
    file_record.status = 'processing'
    session.commit()
    
    # markitdown requires a physical file. 
    # Create a temporary file with the correct extension to process it.
    ext = f".{file_record.file_type}" if file_record.file_type else ""
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        temp_file.write(file_record.original_file_data)
        temp_path = temp_file.name
        
    converter = DocumentConverter()
    result = converter.convert_file(temp_path)
    
    # Delete the temporary physical file immediately after parsing
    os.remove(temp_path)
    
    # Save the markdown directly back into the database
    if file_record:
        file_record.status = result['status']
        if result['status'] == 'completed':
            file_record.md_content = result['md_content']
        else:
            file_record.error_message = result.get('error', 'Unknown error')
        session.commit()
    
    session.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400

    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({"error": "No files selected"}), 400

    batch_uuid = str(uuid.uuid4())
    db = SessionLocal()
    
    new_batch = BatchHistory(batch_uuid=batch_uuid)
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)

    for file in files:
        # Read the file data into memory instead of saving locally
        file_data = file.read()
        
        file_record = FileConversion(
            batch_id=new_batch.id,
            original_filename=file.filename,
            file_type=file.filename.split('.')[-1].lower(),
            original_file_data=file_data
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        # Pass only the record ID to the worker
        executor.submit(process_file_task, file_record.id, DATABASE_URL)

    db.close()
    return jsonify({
        "message": f"{len(files)} files queued for conversion.",
        "batch_id": batch_uuid
    }), 202

@app.route('/history', methods=['GET'])
def get_history():
    db = SessionLocal()
    batches = db.query(BatchHistory).order_by(BatchHistory.created_at.desc()).all()
    
    history_data = []
    for batch in batches:
        files_data = [{
            "id": f.id,
            "filename": f.original_filename,
            "status": f.status,
            "error": f.error_message
        } for f in batch.files]
        
        history_data.append({
            "batch_uuid": batch.batch_uuid,
            "created_at": batch.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "files": files_data
        })
        
    db.close()
    return jsonify(history_data)

@app.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    db = SessionLocal()
    file_record = db.query(FileConversion).filter(FileConversion.id == file_id).first()
    
    if not file_record or not file_record.md_content:
        db.close()
        return "File not found or still processing", 404
        
    # Convert DB text back to bytes
    md_bytes = file_record.md_content.encode('utf-8')
    out_filename = f"{os.path.splitext(file_record.original_filename)[0]}.md"
    
    db.close()
    return send_file(
        io.BytesIO(md_bytes),
        mimetype='text/markdown',
        as_attachment=True,
        download_name=out_filename
    )

@app.route('/download_batch/<string:batch_uuid>', methods=['GET'])
def download_batch(batch_uuid):
    db = SessionLocal()
    batch = db.query(BatchHistory).filter(BatchHistory.batch_uuid == batch_uuid).first()
    
    if not batch:
        db.close()
        return "Batch not found", 404
        
    # Create an in-memory zip file
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for f in batch.files:
            if f.status == 'completed' and f.md_content:
                md_bytes = f.md_content.encode('utf-8')
                out_filename = f"{os.path.splitext(f.original_filename)[0]}.md"
                zf.writestr(out_filename, md_bytes)
                
    memory_file.seek(0)
    db.close()
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"Batch_Files_{batch.created_at.strftime('%Y%m%d_%H%M%S')}.zip"
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)