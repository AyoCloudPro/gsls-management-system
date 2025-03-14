from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
# import pdfkit
import subprocess
import time
from flask import send_from_directory
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_login import LoginManager
from flask_login import login_required, current_user, UserMixin, logout_user, login_user
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from forms import DeleteAdminForm, AddTeacherForm, LoginForm, StudentForm, EditStudentForm, EnterScoresForm, ManageSubjectsForm, RemoveSubjectForm
from flask_migrate import Migrate

import os
import pymysql
pymysql.install_as_MySQLdb()

# Load .env file
# ====================
load_dotenv()

# Manually set the path to wkhtmltopdf
# WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

# Ensure Flask uses this path
# For local testing
# config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH) 
#  ----------------------
# For production
# config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

# Example usage
# pdfkit.from_string("Hello, Flask!", "flask_test.pdf", configuration=config)


# Get values from environment variables
# =======================================
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

hashed_password = generate_password_hash(ADMIN_PASSWORD)
print("Hashed Password:", hashed_password)


# App config
# =========================
app = Flask(__name__)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'my-super-secret-key')
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db = SQLAlchemy(app)
migrate = Migrate(app, db)


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
    teacher_comment = db.Column(db.Text, nullable=True)
    admin_comment = db.Column(db.String(255), nullable=True)

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
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    VALID_ROLES = ['main_admin', 'school_admin', 'teacher']
    role = db.Column(db.String(50), nullable=False)  

    def __init__(self, username, password, role):
        if role not in self.VALID_ROLES:
            raise ValueError("Invalid role")
        self.username = username.lower()
        self.set_password(password)
        self.role = role

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role in ["main_admin", "school_admin"]


# Subject per Class module
# ==========================
class ClassSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_class = db.Column(db.String(50), nullable=False)  
    subject = db.Column(db.String(100), nullable=False)  


# TO calulate percentage
# ==========================
def get_admin_comment(percentage):
    if percentage >= 80:
        return "Excellent performance! Keep it up."
    elif percentage >= 70:
        return "Very good! Keep striving for excellence."
    elif percentage >= 60:
        return "Good performance. Could do better next term."
    elif percentage >= 50:
        return "Fair result. Work harder next term."
    elif percentage >= 40:
        return "Poor result. Must work hard to improve on this performance."
    elif percentage >= 30:
        return "Very poor result. Must work hard to improve on this performance."
    else:
        return "Advised to repeat."



# Role-based access control decorator
# ===================================
def role_required(*required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('You need to log in first.', 'danger')
                return redirect(url_for('login'))

            user = User.query.get(session['user_id'])
            print(f"🔍 Checking role for user: {user.username}, Role: {user.role}")  # Debugging

            if not user or user.role not in required_roles:
                flash('Unauthorized access!', 'danger')
                print(f"🚫 Access denied for {user.username} (Role: {user.role})")  # Debugging
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# To generate CSRF token
# ===========================
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = os.urandom(24).hex()  
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token  # Makes the token available in all templates


# Login manager 
# ======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Login Route
# ======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():  # Flask-WTF automatically checks CSRF token
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        print(request.form)

        if not user or not user.check_password(password):
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        session['user_id'] = user.id
        session['role'] = user.role  

        return redirect(url_for('dashboard'))

    return render_template('login.html', form=form)  


# Logout Route
# ======================
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


# Dashboard Route
# ====================
@app.route('/dashboard')
@login_required
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    total_students = Student.query.count()
    total_subjects = ClassSubject.query.count()
    total_admins = User.query.filter_by(role='school_admin').count()
    total_teachers = User.query.filter_by(role='teacher').count()

    return render_template(
        'dashboard.html',
        role=session['role'],  
        total_students=total_students,
        total_subjects=total_subjects,
        total_admins=total_admins,
        total_teachers=total_teachers
    )


# Debug Route
# =====================
@app.route('/debug_session')
def debug_session():
    return {
        "user_id": session.get('user_id'),
        "role": session.get('role'),
        "authenticated": current_user.is_authenticated
    }


# Route to manage admins (Main Admin Only)
# ===========================================
@app.route('/manage_admins', methods=['GET', 'POST'])
@login_required
@role_required("main_admin")
def manage_admins():
    form = DeleteAdminForm()  # Create an instance of the form

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = "main_admin" if request.form.get('is_main_admin') == "1" else "school_admin"

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!", "danger")
        else:
            new_admin = User(username=username, password=password, role=role)
            new_admin.set_password(password)
            db.session.add(new_admin)
            db.session.commit()
            flash("Admin added successfully!", "success")

        return redirect(url_for('manage_admins'))

    admins = User.query.all()
    return render_template('manage_admins.html', admins=admins, form=form)  


# Route to delete an admin (except the main admin themselves)
# =================================================================
@app.route('/delete_admin/<int:admin_id>', methods=['POST'])
@login_required
@role_required("main_admin")
def delete_admin(admin_id):
    form = DeleteAdminForm()  # Initialize the Flask-WTF form

    if form.validate_on_submit():  # Ensure CSRF protection is working
        admin = User.query.get_or_404(admin_id)
        if admin.role == "main_admin":
            flash('You cannot delete the main admin!', 'danger')
            return redirect(url_for('manage_admins'))

        db.session.delete(admin)
        db.session.commit()
        flash('Admin deleted successfully!', 'success')
    else:
        flash('CSRF token missing or invalid.', 'danger')

    return redirect(url_for('manage_admins'))


# Route to manage teachers (both admins)
# ===============================
@app.route('/manage_teachers', methods=['GET', 'POST'])
@login_required
@role_required("main_admin", "school_admin")
def manage_teachers():
    form = AddTeacherForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!", "danger")
        else:
            new_teacher = User(username=username, password=password, role="teacher")
            new_teacher.set_password(password)
            db.session.add(new_teacher)
            db.session.commit()
            flash("Teacher added successfully!", "success")

        return redirect(url_for('manage_teachers'))

    teachers = User.query.filter_by(role="teacher").all()
    return render_template('manage_teachers.html', teachers=teachers, form=form)


# Route to delete teachers (both admins)
# =======================================
@app.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
@login_required
@role_required("main_admin", "school_admin") 
def delete_teacher(teacher_id):
    teacher = User.query.get_or_404(teacher_id)

    db.session.delete(teacher)
    db.session.commit()
    flash('Teacher deleted successfully!', 'success')

    return redirect(url_for('manage_teachers'))


# Route to student management page
# ===================================
@app.route('/')
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))  
    students = Student.query.all()
    return render_template('index.html', students=students)


# Route to add students
# ================================
@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    form = StudentForm()

    if form.validate_on_submit():
        new_student = Student(
            name=form.name.data,
            reg_num=form.reg_num.data,
            student_class=form.student_class.data,
            age=form.age.data,
            gender=form.gender.data,
            attendance=form.attendance.data
        )

        db.session.add(new_student)
        db.session.commit()
        flash("Student added successfully!", "success") 
        return redirect(url_for('index'))

    return render_template('add_student.html', form=form)


# Route to edit students
# =============================
@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = EditStudentForm(obj=student)  # Pre-populate the form with student data

    if form.validate_on_submit():
        student.name = form.name.data
        student.reg_num = form.reg_num.data
        student.student_class = form.student_class.data
        student.age = form.age.data
        student.gender = form.gender.data
        student.attendance = form.attendance.data

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_student.html', student=student, form=form)


# Route to delete students
# ===============================
@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
@role_required("main_admin")
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('index'))


# Route to manage subjects
# =============================
@app.route('/manage_subjects', methods=['GET', 'POST'])
def manage_subjects():
    ordered_classes = [
        "Pre School", "Pre School 2",
        "Level 1", "Level 2", "Level 3",
        "Primary 1", "Primary 2", "Primary 3", "Primary 4", "Primary 5",
        "JSS 1", "JSS 2"
    ]

    existing_classes = [cs.student_class for cs in ClassSubject.query.distinct(ClassSubject.student_class)]
    classes = [cls for cls in ordered_classes if cls in existing_classes or cls in ordered_classes]

    form = ManageSubjectsForm()
    form.class_name.choices = [(cls, cls) for cls in classes]

    class_subjects = {class_name: ClassSubject.query.filter_by(student_class=class_name).all() for class_name in classes}

    if form.validate_on_submit():
        class_name = form.class_name.data
        subject = form.subject.data

        if not ClassSubject.query.filter_by(student_class=class_name, subject=subject).first():
            new_subject = ClassSubject(student_class=class_name, subject=subject)
            db.session.add(new_subject)
            db.session.commit()

        return redirect(url_for('manage_subjects'))

    return render_template('manage_subjects.html', classes=classes, class_subjects=class_subjects, form=form)


# Route to remove subjects
# =========================
@app.route('/remove_subject/<int:mapping_id>', methods=['POST'])
def remove_subject(mapping_id):
    subject_entry = ClassSubject.query.get_or_404(mapping_id)
    db.session.delete(subject_entry)
    db.session.commit()
    flash("Subject removed successfully!", "success")
    return redirect(url_for('manage_subjects'))


# Route to enter scores
# =========================
@app.route('/enter_scores/<int:student_id>', methods=['GET', 'POST'])
@login_required
def enter_scores(student_id):
    student = Student.query.get_or_404(student_id)
    subjects = [cs.subject for cs in ClassSubject.query.filter(func.lower(ClassSubject.student_class) == func.lower(student.student_class)).all()]
    
    # Create form instance
    form = EnterScoresForm()

    # Dynamically add subject fields
    for subject in subjects:
        setattr(EnterScoresForm, f"{subject}_first_test", IntegerField("1st Test", validators=[NumberRange(0, 20)]))
        setattr(EnterScoresForm, f"{subject}_second_test", IntegerField("2nd Test", validators=[NumberRange(0, 20)]))
        setattr(EnterScoresForm, f"{subject}_class_assessment", IntegerField("Class Assessment", validators=[NumberRange(0, 5)]))
        setattr(EnterScoresForm, f"{subject}_home_assessment", IntegerField("Home Assessment", validators=[NumberRange(0, 5)]))
        setattr(EnterScoresForm, f"{subject}_exam", IntegerField("Exam", validators=[NumberRange(0, 50)]))

    # If form is submitted
    if form.validate_on_submit():
        total_score = 0
        max_score = len(subjects) * 100
        teacher_comment = form.teacher_comment.data.strip()

        for subject in subjects:
            first_test = getattr(form, f"{subject}_first_test").data or 0
            second_test = getattr(form, f"{subject}_second_test").data or 0
            class_assessment = getattr(form, f"{subject}_class_assessment").data or 0
            home_assessment = getattr(form, f"{subject}_home_assessment").data or 0
            exam = getattr(form, f"{subject}_exam").data or 0

            total_subject_score = first_test + second_test + class_assessment + home_assessment + exam
            total_score += total_subject_score

            score = Score.query.filter_by(student_id=student_id, subject=subject).first()
            if not score:
                score = Score(student_id=student_id, subject=subject)
                db.session.add(score)
            
            score.first_test = first_test
            score.second_test = second_test
            score.class_assessment = class_assessment
            score.home_assessment = home_assessment
            score.exam = exam
            score.teacher_comment = teacher_comment

        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        admin_comment = get_admin_comment(percentage)

        for score in Score.query.filter_by(student_id=student_id).all():
            score.admin_comment = admin_comment

        db.session.commit()

        if form.submit_view.data:
            return redirect(url_for('view_report', student_id=student_id))
        else:
            flash("Scores saved successfully!", "success")
            return redirect(url_for('enter_scores', student_id=student_id))

    # Load existing scores into the form
    scores = {score.subject: score for score in Score.query.filter_by(student_id=student_id).all()}
    for subject in subjects:
        if subject in scores:
            getattr(form, f"{subject}_first_test").data = scores[subject].first_test
            getattr(form, f"{subject}_second_test").data = scores[subject].second_test
            getattr(form, f"{subject}_class_assessment").data = scores[subject].class_assessment
            getattr(form, f"{subject}_home_assessment").data = scores[subject].home_assessment
            getattr(form, f"{subject}_exam").data = scores[subject].exam

    return render_template('enter_scores.html', student=student, subjects=subjects, form=form)


# Route to view report card
# ===========================
@app.route('/view_report/<int:student_id>')
@login_required
def view_report(student_id):
    student = Student.query.get_or_404(student_id)
    subjects = [cs.subject for cs in ClassSubject.query.filter_by(student_class=student.student_class).all()]
    scores = Score.query.filter_by(student_id=student_id).filter(Score.subject.in_(subjects)).all()
    
    grand_total = sum(score.total_score for score in scores)
    max_total = len(subjects) * 100
    percentage = (grand_total / max_total) * 100 if max_total > 0 else 0

    # Fetch stored admin comment (from any subject since it’s the same for all)
    admin_comment = scores[0].admin_comment if scores else "No scores available."

    return render_template('report.html', student=student, scores=scores, grand_total=grand_total, percentage=percentage, admin_comment=admin_comment)


# Route to download report card
# ===================================
# @app.route('/download_report/<path:reg_num>')
# @login_required
# def download_report(reg_num):
#     print(f"Received reg_num: {reg_num}")

#     student = Student.query.filter_by(reg_num=reg_num).first()
#     if not student:
#         print("Student not found!")
#         return "Student not found", 404

#     scores = Score.query.filter_by(student_id=student.id).all()
#     grand_total = sum(score.total_score for score in scores)
#     percentage = (grand_total / (15 * 100)) * 100

#     rendered = render_template(
#         'report.html',
#         student=student,
#         scores=scores,
#         grand_total=grand_total,
#         percentage=percentage
#     )

#     print(rendered)

#     #  Ensure folder exists
#     pdf_folder = "generated_pdfs"
#     if not os.path.exists(pdf_folder):
#         os.makedirs(pdf_folder)

#     # 100% Safe Filename: Replace EVERYTHING bad
#     safe_reg_num = re.sub(r'[^a-zA-Z0-9_-]', '-', reg_num)  # Only allow letters, numbers, _ and -

#     #Print new filename for debugging
#     print(f"Safe filename: {safe_reg_num}")

#     # Now use the "safe" registration number for file names
#     html_path = os.path.join(pdf_folder, f"report_{safe_reg_num}.html")
#     pdf_path = os.path.join(pdf_folder, f"report_{safe_reg_num}.pdf")

#     print(f"Saving HTML file to: {html_path}")  # Debug print

#     # Save the HTML to a file
#     with open(html_path, "w", encoding="utf-8") as f:
#         f.write(rendered)

#     options = {
#         'enable-local-file-access': '',
#         'disable-smart-shrinking': '',
#         'load-error-handling': 'ignore'
#     }

#     # Print command before running pdfkit
#     print(f"Running wkhtmltopdf to generate: {html_path}")

#     try:
#         # Convert the saved HTML file to a PDF
#         pdfkit.from_file(html_path, pdf_path, configuration=config, options=options)
#         print(f"PDF successfully generated: {pdf_path}")
#     except Exception as e:
#         print(f"PDF generation failed: {e}")  # Print error
#         return f"PDF generation failed: {e}", 500

#     return send_file(pdf_path, as_attachment=True)


# Route to images
# ============================
@app.route('/static/<path:filename>')
@login_required
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables exist before running
