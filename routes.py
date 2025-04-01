from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Patient, Doctor, Appointment, MedicalRecord, Prescription, Medication
from forms import LoginForm, RegistrationForm, PatientProfileForm, DoctorProfileForm, AppointmentForm, MedicalRecordForm, PrescriptionForm, MedicationForm
from datetime import datetime
import logging

# Add context processor to make datetime available in all templates
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user)
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to the page the user was trying to access
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            if user.is_admin():
                next_page = url_for('admin_dashboard')
            elif user.is_doctor():
                next_page = url_for('doctor_dashboard')
            else:
                next_page = url_for('patient_dashboard')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role='patient')
        user.set_password(form.password.data)
        
        # Create a patient profile for the user
        patient = Patient(
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        
        user.patient_profile = patient
        
        db.session.add(user)
        db.session.add(patient)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Dashboard routes
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_doctor():
        return redirect(url_for('doctor_dashboard'))
    else:
        return redirect(url_for('patient_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get counts for dashboard statistics
    patient_count = Patient.query.count()
    doctor_count = Doctor.query.count()
    appointment_count = Appointment.query.count()
    prescription_count = Prescription.query.count()
    
    return render_template(
        'admin/dashboard.html', 
        patient_count=patient_count, 
        doctor_count=doctor_count, 
        appointment_count=appointment_count,
        prescription_count=prescription_count
    )

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if not current_user.is_doctor():
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    if not current_user.doctor_profile:
        flash('Please complete your doctor profile first.', 'warning')
        return redirect(url_for('doctor_profile'))
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id,
        status='scheduled'
    ).order_by(Appointment.appointment_datetime).limit(5).all()
    
    # Get recent medical records
    recent_records = MedicalRecord.query.filter_by(
        doctor_id=current_user.doctor_profile.id
    ).order_by(MedicalRecord.date.desc()).limit(5).all()
    
    # Get recent prescriptions
    recent_prescriptions = Prescription.query.filter_by(
        doctor_id=current_user.doctor_profile.id
    ).order_by(Prescription.created_at.desc()).limit(5).all()
    
    return render_template(
        'doctor/dashboard.html',
        appointments=upcoming_appointments,
        records=recent_records,
        prescriptions=recent_prescriptions
    )

@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if not current_user.is_patient():
        flash('Access denied. This page is for patients only.', 'danger')
        return redirect(url_for('dashboard'))
    
    if not current_user.patient_profile:
        flash('Please complete your patient profile first.', 'warning')
        return redirect(url_for('patient_profile'))
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.patient_profile.id,
        status='scheduled'
    ).order_by(Appointment.appointment_datetime).all()
    
    # Get recent medical records
    recent_records = MedicalRecord.query.filter_by(
        patient_id=current_user.patient_profile.id
    ).order_by(MedicalRecord.date.desc()).limit(5).all()
    
    # Get active prescriptions
    active_prescriptions = Prescription.query.filter_by(
        patient_id=current_user.patient_profile.id,
        status='active'
    ).all()
    
    return render_template(
        'patient/dashboard.html',
        appointments=upcoming_appointments,
        records=recent_records,
        prescriptions=active_prescriptions
    )

# Patient routes
@app.route('/patient/profile', methods=['GET', 'POST'])
@login_required
def patient_profile():
    if not current_user.is_patient():
        flash('Only patients can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    patient = current_user.patient_profile
    if not patient:
        patient = Patient(user_id=current_user.id)
    
    form = PatientProfileForm(obj=patient)
    
    if form.validate_on_submit():
        form.populate_obj(patient)
        
        if not patient.id:  # If it's a new patient profile
            db.session.add(patient)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('patient_dashboard'))
    
    return render_template('patient/profile.html', form=form)

@app.route('/patient/appointments')
@login_required
def patient_appointments():
    if not current_user.is_patient():
        flash('Only patients can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    if not current_user.patient_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('patient_profile'))
    
    # Get all patient appointments
    appointments = Appointment.query.filter_by(
        patient_id=current_user.patient_profile.id
    ).order_by(Appointment.appointment_datetime.desc()).all()
    
    return render_template('patient/appointments.html', appointments=appointments)

@app.route('/patient/book-appointment', methods=['GET', 'POST'])
@login_required
def patient_book_appointment():
    if not current_user.is_patient():
        flash('Only patients can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    if not current_user.patient_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('patient_profile'))
    
    form = AppointmentForm()
    # Populate doctor choices
    form.doctor_id.choices = [(d.id, f"Dr. {d.first_name} {d.last_name} - {d.specialization}") 
                             for d in Doctor.query.all()]
    
    if form.validate_on_submit():
        appointment = Appointment(
            patient_id=current_user.patient_profile.id,
            doctor_id=form.doctor_id.data,
            appointment_datetime=form.appointment_datetime.data,
            reason=form.reason.data,
            notes=form.notes.data,
            status='scheduled'
        )
        
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment scheduled successfully!', 'success')
        return redirect(url_for('patient_appointments'))
    
    return render_template('patient/book_appointment.html', form=form)

@app.route('/patient/medical-records')
@login_required
def patient_medical_records():
    if not current_user.is_patient():
        flash('Only patients can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    if not current_user.patient_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('patient_profile'))
    
    # Get all medical records for the patient
    records = MedicalRecord.query.filter_by(
        patient_id=current_user.patient_profile.id
    ).order_by(MedicalRecord.date.desc()).all()
    
    return render_template('patient/medical_records.html', records=records)

@app.route('/patient/prescriptions')
@login_required
def patient_prescriptions():
    if not current_user.is_patient():
        flash('Only patients can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    if not current_user.patient_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('patient_profile'))
    
    # Get all prescriptions for the patient
    prescriptions = Prescription.query.filter_by(
        patient_id=current_user.patient_profile.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return render_template('patient/prescriptions.html', prescriptions=prescriptions)

# Doctor routes
@app.route('/doctor/profile', methods=['GET', 'POST'])
@login_required
def doctor_profile():
    if not current_user.is_doctor():
        flash('Only doctors can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    doctor = current_user.doctor_profile
    if not doctor:
        doctor = Doctor(user_id=current_user.id)
    
    form = DoctorProfileForm(obj=doctor)
    
    if form.validate_on_submit():
        form.populate_obj(doctor)
        
        if not doctor.id:  # If it's a new doctor profile
            db.session.add(doctor)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor_dashboard'))
    
    return render_template('doctor/profile.html', form=form)

@app.route('/doctor/appointments')
@login_required
def doctor_appointments():
    if not current_user.is_doctor():
        flash('Only doctors can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    if not current_user.doctor_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('doctor_profile'))
    
    # Get all doctor appointments
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.doctor_profile.id
    ).order_by(Appointment.appointment_datetime).all()
    
    return render_template('doctor/appointments.html', appointments=appointments)

@app.route('/doctor/appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def doctor_manage_appointment(appointment_id):
    if not current_user.is_doctor():
        flash('Only doctors can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Check if this appointment belongs to the doctor
    if appointment.doctor_id != current_user.doctor_profile.id:
        flash('You do not have permission to manage this appointment.', 'danger')
        return redirect(url_for('doctor_appointments'))
    
    form = AppointmentForm(obj=appointment)
    
    if request.method == 'GET':
        # Pre-select the current doctor
        form.doctor_id.data = appointment.doctor_id
    
    # Populate doctor choices
    form.doctor_id.choices = [(d.id, f"Dr. {d.first_name} {d.last_name} - {d.specialization}") 
                             for d in Doctor.query.all()]
    
    if form.validate_on_submit():
        appointment.doctor_id = form.doctor_id.data
        appointment.appointment_datetime = form.appointment_datetime.data
        appointment.reason = form.reason.data
        appointment.notes = form.notes.data
        appointment.status = form.status.data
        
        db.session.commit()
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('doctor_appointments'))
    
    return render_template('doctor/manage_appointment.html', form=form, appointment=appointment)

@app.route('/doctor/patients')
@login_required
def doctor_patients():
    if not current_user.is_doctor():
        flash('Only doctors can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    if not current_user.doctor_profile:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('doctor_profile'))
    
    # Get patients who have appointments with this doctor
    patients = Patient.query.join(Appointment).filter(
        Appointment.doctor_id == current_user.doctor_profile.id
    ).distinct().all()
    
    return render_template('doctor/patients.html', patients=patients)

@app.route('/doctor/patient/<int:patient_id>')
@login_required
def doctor_view_patient(patient_id):
    if not current_user.is_doctor():
        flash('Only doctors can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Get patient's appointments with this doctor
    appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        doctor_id=current_user.doctor_profile.id
    ).order_by(Appointment.appointment_datetime.desc()).all()
    
    # Get patient's medical records created by this doctor
    medical_records = MedicalRecord.query.filter_by(
        patient_id=patient.id,
        doctor_id=current_user.doctor_profile.id
    ).order_by(MedicalRecord.date.desc()).all()
    
    # Get patient's prescriptions issued by this doctor
    prescriptions = Prescription.query.filter_by(
        patient_id=patient.id,
        doctor_id=current_user.doctor_profile.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return render_template(
        'doctor/view_patient.html',
        patient=patient,
        appointments=appointments,
        medical_records=medical_records,
        prescriptions=prescriptions
    )

@app.route('/doctor/add-medical-record/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def doctor_add_medical_record(patient_id):
    if not current_user.is_doctor():
        flash('Only doctors can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    patient = Patient.query.get_or_404(patient_id)
    form = MedicalRecordForm()
    
    if form.validate_on_submit():
        record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=current_user.doctor_profile.id,
            diagnosis=form.diagnosis.data,
            symptoms=form.symptoms.data,
            treatment=form.treatment.data,
            notes=form.notes.data
        )
        
        db.session.add(record)
        db.session.commit()
        flash('Medical record added successfully!', 'success')
        return redirect(url_for('doctor_view_patient', patient_id=patient.id))
    
    return render_template('doctor/add_medical_record.html', form=form, patient=patient)

@app.route('/doctor/add-prescription/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def doctor_add_prescription(patient_id):
    if not current_user.is_doctor():
        flash('Only doctors can access this page.', 'warning')
        return redirect(url_for('dashboard'))
    
    patient = Patient.query.get_or_404(patient_id)
    form = PrescriptionForm()
    
    # Populate medication choices
    form.medication_name.choices = [(m.name, m.name) for m in Medication.query.all()]
    
    if form.validate_on_submit():
        prescription = Prescription(
            patient_id=patient.id,
            doctor_id=current_user.doctor_profile.id,
            medication_name=form.medication_name.data,
            dosage=form.dosage.data,
            frequency=form.frequency.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            instructions=form.instructions.data,
            status='active'
        )
        
        db.session.add(prescription)
        db.session.commit()
        flash('Prescription added successfully!', 'success')
        return redirect(url_for('doctor_view_patient', patient_id=patient.id))
    
    return render_template('doctor/add_prescription.html', form=form, patient=patient)

# Admin routes
@app.route('/admin/patients')
@login_required
def admin_manage_patients():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    patients = Patient.query.all()
    return render_template('admin/manage_patients.html', patients=patients)

@app.route('/admin/doctors')
@login_required
def admin_manage_doctors():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    doctors = Doctor.query.all()
    return render_template('admin/manage_doctors.html', doctors=doctors)

@app.route('/admin/medications', methods=['GET', 'POST'])
@login_required
def admin_manage_medications():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = MedicationForm()
    
    if form.validate_on_submit():
        # Check for duplicate medication name
        existing_medication = Medication.query.filter_by(name=form.name.data).first()
        if existing_medication and request.form.get('medication_id') != str(existing_medication.id):
            flash(f'A medication with name {form.name.data} already exists.', 'danger')
        else:
            if request.form.get('medication_id'):  # Edit existing medication
                medication = Medication.query.get_or_404(int(request.form.get('medication_id')))
                form.populate_obj(medication)
                db.session.commit()
                flash(f'Medication {medication.name} updated successfully!', 'success')
            else:  # Create new medication
                medication = Medication()
                form.populate_obj(medication)
                db.session.add(medication)
                db.session.commit()
                flash(f'Medication {medication.name} created successfully!', 'success')
            
            # Reset form after submission
            form = MedicationForm()
    
    medications = Medication.query.all()
    return render_template('admin/manage_medications.html', form=form, medications=medications)

@app.route('/admin/medication/<int:medication_id>/edit', methods=['GET'])
@login_required
def admin_edit_medication(medication_id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    medication = Medication.query.get_or_404(medication_id)
    form = MedicationForm(obj=medication)
    
    medications = Medication.query.all()
    return render_template(
        'admin/manage_medications.html', 
        form=form, 
        medications=medications, 
        edit_medication=medication
    )

@app.route('/admin/medication/<int:medication_id>/delete', methods=['POST'])
@login_required
def admin_delete_medication(medication_id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    medication = Medication.query.get_or_404(medication_id)
    
    # Check if medication is in use
    prescriptions = Prescription.query.filter_by(medication_name=medication.name).first()
    if prescriptions:
        flash(f'Cannot delete {medication.name}. It is used in prescriptions.', 'danger')
    else:
        # Delete the medication
        db.session.delete(medication)
        db.session.commit()
        flash(f'Medication {medication.name} has been deleted.', 'success')
    
    return redirect(url_for('admin_manage_medications'))

@app.route('/admin/create-doctor', methods=['GET', 'POST'])
@login_required
def admin_create_doctor():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('admin/create_doctor.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use a different one.', 'danger')
            return render_template('admin/create_doctor.html', form=form)
        
        # Create new doctor user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role='doctor'
        )
        user.set_password(form.password.data)
        
        # Create doctor profile 
        doctor = Doctor(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            specialization="General Medicine",  # Default value, can be updated later
            license_number="TBD"  # Default value, should be updated later
        )
        
        user.doctor_profile = doctor
        
        db.session.add(user)
        db.session.add(doctor)
        db.session.commit()
        
        flash('Doctor account created successfully!', 'success')
        return redirect(url_for('admin_manage_doctors'))
    
    return render_template('admin/create_doctor.html', form=form)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
