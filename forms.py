from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User
from datetime import date

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken. Please use a different username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')

class PatientProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ], validators=[Optional()])
    blood_type = SelectField('Blood Type', choices=[
        ('', 'Select Blood Type'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('unknown', 'Unknown')
    ], validators=[Optional()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=200)])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=100)])
    insurance_info = StringField('Insurance Information', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Update Patient Profile')

class DoctorProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    specialization = StringField('Specialization', validators=[DataRequired(), Length(max=100)])
    license_number = StringField('License Number', validators=[DataRequired(), Length(max=50)])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    office_location = StringField('Office Location', validators=[Optional(), Length(max=200)])
    bio = TextAreaField('Biography', validators=[Optional()])
    submit = SubmitField('Update Doctor Profile')

class AppointmentForm(FlaskForm):
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    appointment_datetime = DateField('Appointment Date', format='%Y-%m-%d', validators=[DataRequired()])
    reason = StringField('Reason for Visit', validators=[DataRequired(), Length(max=200)])
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='scheduled', validators=[DataRequired()])
    submit = SubmitField('Schedule Appointment')

class MedicalRecordForm(FlaskForm):
    diagnosis = StringField('Diagnosis', validators=[DataRequired(), Length(max=200)])
    symptoms = TextAreaField('Symptoms', validators=[Optional()])
    treatment = TextAreaField('Treatment Plan', validators=[Optional()])
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    submit = SubmitField('Save Medical Record')

class PrescriptionForm(FlaskForm):
    medication_name = SelectField('Medication', validators=[DataRequired()])
    dosage = StringField('Dosage', validators=[DataRequired(), Length(max=50)])
    frequency = StringField('Frequency (e.g. twice daily)', validators=[DataRequired(), Length(max=50)])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date (if applicable)', format='%Y-%m-%d', validators=[Optional()])
    instructions = TextAreaField('Special Instructions', validators=[Optional()])
    submit = SubmitField('Issue Prescription')

class MedicationForm(FlaskForm):
    name = StringField('Medication Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    manufacturer = StringField('Manufacturer', validators=[Optional(), Length(max=100)])
    common_dosages = StringField('Common Dosages', validators=[Optional(), Length(max=200)])
    side_effects = TextAreaField('Side Effects', validators=[Optional()])
    contraindications = TextAreaField('Contraindications', validators=[Optional()])
    submit = SubmitField('Save Medication')
