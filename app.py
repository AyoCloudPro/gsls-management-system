from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from flask_sqlalchemy import SQLAlchemy
import pdfkit
import subprocess
import time
from flask import send_from_directory
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_login import LoginManager
from flask_login import login_required, current_user, UserMixin, logout_user, login_user
from dotenv import load_dotenv

import os


# wkhtmltopdf location
# ==============================
config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
options = {
    'enable-local-file-access': None
}


# Load .env file
# ====================
load_dotenv()  


# App config
# =========================
app = Flask(__name__)
login_manager = LoginManager(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)


# Login required decorator
# ==========================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            print("🔴 User not logged in! Redirecting to login...")  # Debugging
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Student Model
# ========================
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    reg_num = db.Column(db.String(20), unique=True, nullable=False)
    student_class = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    attendance = db.Column(db.String(20), nullable=False)


# Score Model
# ====================
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    first_test = db.Column(db.Integer, default=0)
    second_test = db.Column(db.Integer, default=0)
    class_assessment = db.Column(db.Integer, default=0)
    home_assessment = db.Column(db.Integer, default=0)
    exam = db.Column(db.Integer, default=0)

    @property
    def total_score(self):
        return self.first_test + self.second_test + self.class_assessment + self.home_assessment + self.exam

    @property
    def grade(self):
        score = self.total_score
        if score >= 75:
            return 'A'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'F'


# Admin Module
# ==================
class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_main_admin = db.Column(db.Boolean, default=False)  # ✅ True = Developer, False = School Admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ✅ Create default admins if they don't exist
# with app.app_context():
#     db.create_all()

#     dev_password = os.getenv("DEV_ADMIN_PASSWORD", "default_password")
#     school_password = os.getenv("SCHOOL_ADMIN_PASSWORD", "default_password")

#     if not Admin.query.filter_by(username="developer").first():
#         dev_admin = Admin(username="developer", is_main_admin=True)  # You = Main Admin
#         dev_admin.set_password(dev_password)
#         db.session.add(dev_admin)

#     if not Admin.query.filter_by(username="school").first():
#         school_admin = Admin(username="school", is_main_admin=False)  # School Admin
#         school_admin.set_password(school_password)
#         db.session.add(school_admin)

#     db.session.commit()
#     print("✅ Default admins created: Developer (dev_password), School Admin (school_password)")

   

# Role-based access control decorator
# ===================================
def role_required(main_admin_required=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'admin_logged_in' not in session:
                return redirect(url_for('login'))
            
            if main_admin_required and not session.get('is_main_admin', False):
                return "Access Denied: You do not have permission to perform this action.", 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Login manager 
# ======================
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


# Login Route
# ======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            session['admin_logged_in'] = True
            session['is_main_admin'] = admin.is_main_admin
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')


# Logout Route
# ======================
@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))


# Dashboard Route
# =============================
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    print("Current User:", current_user.username)
    print("Is Main Admin:", current_user.is_main_admin)  # Debugging

    total_students = Student.query.count()
    total_subjects = db.session.query(Score.subject).distinct().count()
    total_admins = Admin.query.count()
    return render_template('admin_dashboard.html', current_user=current_user, total_students=total_students, total_subjects=total_subjects, total_admins=total_admins)



# Route to manage admins (Main Admin Only)
# ===========================================
@app.route('/manage_admins', methods=['GET', 'POST'])
@login_required
@role_required(main_admin_required=True)
def manage_admins():
    admins = Admin.query.all()
    return render_template('manage_admins.html', admins=admins)


# Route to add a new admin
# ======================================
@app.route('/add_admin', methods=['POST'])
@login_required
@role_required(main_admin_required=True)
def add_admin():
    username = request.form.get('username')
    password = request.form.get('password')
    is_main_admin = request.form.get('is_main_admin') == 'on'
    
    if Admin.query.filter_by(username=username).first():
        flash('Username already exists!', 'danger')
        return redirect(url_for('manage_admins'))
    
    hashed_password = generate_password_hash(password)
    new_admin = Admin(username=username, password=hashed_password, is_main_admin=is_main_admin)
    db.session.add(new_admin)
    db.session.commit()
    flash('New admin added successfully!', 'success')
    return redirect(url_for('manage_admins'))


# Route to delete an admin (except the main admin themselves)
# =================================================================
@app.route('/delete_admin/<int:admin_id>', methods=['POST'])
@login_required
@role_required(main_admin_required=True)
def delete_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    if admin.is_main_admin:
        flash('You cannot delete the main admin!', 'danger')
        return redirect(url_for('manage_admins'))
    
    db.session.delete(admin)
    db.session.commit()
    flash('Admin deleted successfully!', 'success')
    return redirect(url_for('manage_admins'))


# Route to student management page
# ===================================
@app.route('/')
@login_required
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)


# Route to add students
# ================================
@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        reg_num = request.form['reg_num']
        student_class = request.form['student_class']
        age = request.form['age']
        gender = request.form['gender']
        attendance = request.form['attendance']

        new_student = Student(name=name, reg_num=reg_num, student_class=student_class, age=age, gender=gender, attendance=attendance)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add_student.html')


# Route to edit students
# =============================
@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.reg_num = request.form['reg_num']
        student.student_class = request.form['student_class']
        student.age = request.form['age']
        student.gender = request.form['gender']
        student.attendance = request.form['attendance']

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_student.html', student=student)


# Route to delete students
# ===============================
@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
@role_required(main_admin_required=True)
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('index'))


# Route to enter scores
# =========================
@app.route('/enter_scores/<int:student_id>', methods=['GET', 'POST'])
@login_required
def enter_scores(student_id):
    student = Student.query.get_or_404(student_id)
    subjects = ["Mathematics", "English", "Science", "Social Studies", "ICT", "French", "Physical Education", "Art", "Music", "Agriculture", "Home Economics", "Civic Education", "Business Studies", "Religious Studies", "History"]
    
    if request.method == 'POST':
        for subject in subjects:
            first_test = int(request.form.get(f'{subject}_first_test', 0) or 0)
            second_test = int(request.form.get(f'{subject}_second_test', 0) or 0)
            class_assessment = int(request.form.get(f'{subject}_class_assessment', 0) or 0)
            home_assessment = int(request.form.get(f'{subject}_home_assessment', 0) or 0)
            exam = int(request.form.get(f'{subject}_exam', 0) or 0)
            
            score = Score.query.filter_by(student_id=student_id, subject=subject).first()
            if not score:
                score = Score(student_id=student_id, subject=subject)
                db.session.add(score)
            
            score.first_test = first_test
            score.second_test = second_test
            score.class_assessment = class_assessment
            score.home_assessment = home_assessment
            score.exam = exam
        
        db.session.commit()
        return redirect(url_for('view_report', student_id=student_id))
    
    scores = {score.subject: score for score in Score.query.filter_by(student_id=student_id).all()}
    return render_template('enter_scores.html', student=student, subjects=subjects, scores=scores)


# Route to view report card
# ===========================
@app.route('/view_report/<int:student_id>')
@login_required
def view_report(student_id):
    student = Student.query.get_or_404(student_id)
    scores = Score.query.filter_by(student_id=student_id).all()
    grand_total = sum(score.total_score for score in scores)
    percentage = (grand_total / (15 * 100)) * 100  # Assuming 15 subjects, max 100 each

    download_url = url_for('download_report', reg_num=student.reg_num)
    print(f"Download URL: {download_url}")  # Debugging


    return render_template('report.html', student=student, scores=scores, grand_total=grand_total, percentage=percentage, download_url=url_for('download_report', reg_num=student.reg_num))


# Route to download report card
# ===================================
@app.route('/download_report/<path:reg_num>')
@login_required
def download_report(reg_num):
    print(f"Received reg_num: {reg_num}")

    student = Student.query.filter_by(reg_num=reg_num).first()
    if not student:
        print("❌ Student not found!")
        return "Student not found", 404

    scores = Score.query.filter_by(student_id=student.id).all()
    grand_total = sum(score.total_score for score in scores)
    percentage = (grand_total / (15 * 100)) * 100

    rendered = render_template(
        'report.html',
        student=student,
        scores=scores,
        grand_total=grand_total,
        percentage=percentage
    )

    print(rendered)

    # ✅ Ensure folder exists
    pdf_folder = "generated_pdfs"
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)

    # ✅ 100% Safe Filename: Replace EVERYTHING bad
    safe_reg_num = re.sub(r'[^a-zA-Z0-9_-]', '-', reg_num)  # Only allow letters, numbers, _ and -

    # ✅ Print new filename for debugging
    print(f"Safe filename: {safe_reg_num}")

    # ✅ Now use the "safe" registration number for file names
    html_path = os.path.join(pdf_folder, f"report_{safe_reg_num}.html")
    pdf_path = os.path.join(pdf_folder, f"report_{safe_reg_num}.pdf")

    print(f"Saving HTML file to: {html_path}")  # Debug print

    # Save the HTML to a file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    options = {
        'enable-local-file-access': '',
        'disable-smart-shrinking': '',
        'load-error-handling': 'ignore'
    }

    # ✅ Print command before running pdfkit
    print(f"Running wkhtmltopdf to generate: {html_path}")

    try:
        # Convert the saved HTML file to a PDF
        pdfkit.from_file(html_path, pdf_path, configuration=config, options=options)
        print(f"✅ PDF successfully generated: {pdf_path}")
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")  # Print error
        return f"PDF generation failed: {e}", 500

    return send_file(pdf_path, as_attachment=True)


# Route to images
# ============================
@app.route('/static/<path:filename>')
@login_required
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
