import os
import uuid
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import UploadedFile, User
from services.file_processor import FileProcessor
from services.ai_service import AIService
from services.vector_store import VectorStore
from services.pdf_generator import PDFReportGenerator
from google_auth import google_auth

from utils.chart_generator import ChartGenerator
from datetime import datetime

# Initialize services
file_processor = FileProcessor()
ai_service = AIService()
chart_generator = ChartGenerator()
vector_store = VectorStore()
pdf_generator = PDFReportGenerator()


ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=bool(request.form.get('remember')))
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
        
        # Create new user
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/switch-account', methods=['POST'])
@login_required
def switch_account():
    """Handle account switching by authenticating with provided credentials"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash('Email and password are required.', 'error')
        return redirect(url_for('index'))
    
    # Find the user by email
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Account not found. Please check the email address.', 'error')
        return redirect(url_for('index'))
    
    # Verify password
    if not user.check_password(password):
        flash('Invalid password. Please try again.', 'error')
        return redirect(url_for('index'))
    
    # Check if user is active
    if not user.active:
        flash('This account is deactivated. Please contact support.', 'error')
        return redirect(url_for('index'))
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Logout current user and login to the new account
    logout_user()
    login_user(user)
    
    flash(f'Successfully switched to account: {user.username}', 'success')
    return redirect(url_for('index'))

@app.route('/api/recent-accounts')
@login_required
def get_recent_accounts():
    """Get recent accounts for the account switcher"""
    # Get recently active accounts (excluding current user)
    recent_users = User.query.filter(
        User.id != current_user.id,
        User.active == True
    ).order_by(User.last_login.desc()).limit(5).all()
    
    accounts = []
    for user in recent_users:
        accounts.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
        })
    
    return jsonify(accounts)

@app.route('/add-account', methods=['GET', 'POST'])
@login_required
def add_account():
    """Create additional account while staying logged in to current account"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return render_template('auth/add_account.html')
        
        # Check if email exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered', 'error')
            return render_template('auth/add_account.html')
        
        # Create new user
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(f'New account "{username}" created successfully! You can now switch to it.', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/add_account.html')



# Main Routes
@app.route('/')
def index():
    # Public home page - no login required
    if current_user.is_authenticated:
        # Show dashboard for logged-in users
        recent_files = UploadedFile.query.filter_by(user_id=current_user.id).order_by(UploadedFile.upload_date.desc()).limit(5).all()
        return render_template('dashboard.html', recent_files=recent_files)
    else:
        # Show public home page for visitors
        return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    recent_files = UploadedFile.query.filter_by(user_id=current_user.id).order_by(UploadedFile.upload_date.desc()).limit(5).all()
    return render_template('dashboard.html', recent_files=recent_files)



@app.route('/test-upload')
def test_upload():
    return render_template('simple_upload.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')
    
    # Handle POST request for file upload
    # Check if file exists in request
    if 'file' not in request.files:
        flash('No file was uploaded. Please select a file.', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    # Check if file was actually selected
    if not file or file.filename == '' or file.filename is None:
        flash('Please select a file to upload.', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            # Generate unique filename
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Create database record
            uploaded_file = UploadedFile()
            uploaded_file.user_id = current_user.id
            uploaded_file.filename = filename
            uploaded_file.original_filename = file.filename
            uploaded_file.file_path = file_path
            uploaded_file.file_type = file.filename.rsplit('.', 1)[1].lower()
            uploaded_file.file_size = os.path.getsize(file_path)
            db.session.add(uploaded_file)
            db.session.commit()
            
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('analyze_file', file_id=uploaded_file.id))
            
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload PDF, TXT, DOCX, or image files.', 'error')
        return redirect(url_for('index'))

@app.route('/analyze/<int:file_id>')
@login_required
def analyze_file(file_id):
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    if not uploaded_file.analysis_complete:
        try:
            # Process file content
            content = file_processor.extract_text(uploaded_file.file_path, uploaded_file.file_type)
            
            if not content:
                flash('Unable to extract text from file', 'error')
                return redirect(url_for('index'))
            
            # Generate AI analysis
            analysis = ai_service.analyze_lab_report(content)
            
            # Generate chart data if numerical data is found
            chart_data = chart_generator.generate_chart_data(content, analysis)
            
            # Update database with analysis results
            uploaded_file.summary = analysis.get('detailed_summary', '')
            uploaded_file.risk_assessment = analysis.get('overall_health_assessment', '')
            uploaded_file.recommendations = analysis.get('health_tips', '')
            uploaded_file.chart_data = {
                'lab_values_table': analysis.get('lab_values_table', []),
                'chart_data': chart_data
            }
            uploaded_file.analysis_complete = True
            db.session.commit()
            
            # Store content in vector store for RAG
            vector_store.add_document(content, file_id, uploaded_file.original_filename)
            
        except Exception as e:
            flash(f'Error analyzing file: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    return render_template('report.html', file=uploaded_file)



@app.route('/reports')
@login_required
def reports():
    files = UploadedFile.query.filter_by(user_id=current_user.id).order_by(UploadedFile.upload_date.desc()).all()
    return render_template('reports.html', files=files)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/medical-assistant')
@login_required
def medical_assistant():
    return render_template('medical_assistant.html')

@app.route('/ask-medical-question', methods=['POST'])
@login_required
def ask_medical_question():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return {'error': 'Please provide a medical question'}, 400
        
        # Check if question is medical-related using AI service
        if not ai_service.is_medical_query(question):
            return {
                'response': 'I can only answer medical and health-related questions. Please ask about symptoms, conditions, medications, or general health topics.',
                'sources': []
            }
        
        # Search PubMed for relevant articles
        from services.pubmed_service import PubMedService
        pubmed_service = PubMedService()
        pubmed_results = pubmed_service.search_articles(question, max_results=5)
        
        # Generate AI response with PubMed context
        ai_response = ai_service.generate_medical_response(question, pubmed_results)
        
        return {
            'response': ai_response,
            'sources': pubmed_results.get('articles', []) if isinstance(pubmed_results, dict) else []
        }
        
    except Exception as e:
        return {'error': f'Error processing question: {str(e)}'}, 500

@app.route('/delete/<int:file_id>', methods=['GET', 'POST'])
@login_required
def delete_file(file_id):
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    try:
        # Delete physical file
        if os.path.exists(uploaded_file.file_path):
            os.remove(uploaded_file.file_path)
        
        # Delete from vector store
        vector_store.delete_document(file_id)
        

        
        # Delete from database
        db.session.delete(uploaded_file)
        db.session.commit()
        
        flash('File deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('reports'))

@app.route('/ask-report-question', methods=['POST'])
@login_required
def ask_report_question():
    try:
        data = request.get_json()
        question = data.get('question')
        file_id = data.get('file_id')
        
        if not question or not file_id:
            return jsonify({'error': 'Question and file ID are required'}), 400
        
        # Get the uploaded file - ensure it belongs to current user
        uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user.id).first()
        if not uploaded_file:
            return jsonify({'error': 'File not found'}), 404
        
        # Search for similar content in vector store for this specific file
        similar_content = vector_store.search_similar_content(question, file_id=file_id, top_k=3)
        
        # Generate response using AI service with the specific report context
        ai_service = AIService()
        
        # Create context from the file's analysis and similar content
        context_parts = []
        if uploaded_file.summary:
            context_parts.append(f"Report Summary: {uploaded_file.summary}")
        if uploaded_file.risk_assessment:
            context_parts.append(f"Risk Assessment: {uploaded_file.risk_assessment}")
        if uploaded_file.recommendations:
            context_parts.append(f"Recommendations: {uploaded_file.recommendations}")
        if similar_content:
            context_parts.append(f"Relevant Report Content: {similar_content}")
        
        context = "\n\n".join(context_parts)
        
        # Generate response focused on this specific report
        response = ai_service.generate_report_specific_response(question, context, uploaded_file.original_filename)
        
        return jsonify({
            'response': response,
            'file_name': uploaded_file.original_filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

@app.route('/download-report/<int:file_id>')
@login_required
def download_report(file_id):
    """Download comprehensive PDF report"""
    try:
        # Get the uploaded file - ensure it belongs to current user
        uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
        
        if not uploaded_file.analysis_complete:
            flash('Report analysis is not complete yet. Please wait for analysis to finish.', 'warning')
            return redirect(url_for('analyze_file', file_id=file_id))
        
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Generate PDF filename
        safe_filename = secure_filename(uploaded_file.original_filename)
        pdf_filename = f"{safe_filename}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(downloads_dir, pdf_filename)
        
        # Generate PDF report
        pdf_generator.generate_report(uploaded_file, pdf_path)
        
        # Send file for download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('analyze_file', file_id=file_id))


# Register Google OAuth blueprint
app.register_blueprint(google_auth)
