from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Login")


class DeleteAdminForm(FlaskForm):
    csrf_token = HiddenField()  # ✅ CSRF Token Field


class AddTeacherForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Add Teacher")


class StudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    reg_num = StringField('Registration Number', validators=[DataRequired()])
    student_class = SelectField('Class', choices=[
        ('Pre School', 'Pre School'),
        ('Pre School 2', 'Pre School 2'),
        ('Level 1', 'Level 1'),
        ('Level 2', 'Level 2'),
        ('Level 3', 'Level 3'),
        ('Primary 1', 'Primary 1'),
        ('Primary 2', 'Primary 2'),
        ('Primary 3', 'Primary 3'),
        ('Primary 4', 'Primary 4'),
        ('Primary 5', 'Primary 5'),
        ('JSS 1', 'JSS 1'),
        ('JSS 2', 'JSS 2')
    ], validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    attendance = StringField('Attendance', validators=[DataRequired()])
    submit = SubmitField('Add Student')


class EditStudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    reg_num = StringField('Registration Number', validators=[DataRequired()])
    student_class = SelectField('Class', choices=[
        ('Pre School', 'Pre School'),
        ('Pre School 2', 'Pre School 2'),
        ('Level 1', 'Level 1'),
        ('Level 2', 'Level 2'),
        ('Level 3', 'Level 3'),
        ('Primary 1', 'Primary 1'),
        ('Primary 2', 'Primary 2'),
        ('Primary 3', 'Primary 3'),
        ('Primary 4', 'Primary 4'),
        ('Primary 5', 'Primary 5'),
        ('JSS 1', 'JSS 1'),
        ('JSS 2', 'JSS 2')
    ], validators=[DataRequired()])
    
    age = IntegerField('Age', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    attendance = StringField('Attendance', validators=[DataRequired()])
    
    submit = SubmitField('Update Student')


class EnterScoresForm(FlaskForm):
    teacher_comment = TextAreaField("Teacher's Comment")
    teacher_name = StringField("Teacher's Name", validators=[DataRequired()])
    submit_save = SubmitField("Save Scores")
    submit_view = SubmitField("View Report")



class ManageSubjectsForm(FlaskForm):
    class_name = SelectField("Select Class", validators=[DataRequired()])
    subject = StringField("Enter Subject", validators=[DataRequired()])
    submit = SubmitField("Add Subject")



class RemoveSubjectForm(FlaskForm):
    mapping_id = HiddenField()
    submit = SubmitField('Remove')