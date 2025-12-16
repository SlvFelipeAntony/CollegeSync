class User:
    def __init__(self, name, email, hash_password, created_at=None, updated_at=None, birth_date=None, id=None):
        self.id = id
        self.name = name
        self.email = email
        self.birth_date = birth_date
        self.hash_password = hash_password
        self.created_at = created_at
        self.updated_at = updated_at

    def __str__(self):
        return self.name

class Student:
    def __init__(self, registration_number, user_id, id=None):
        self.id = id
        self.registration_number = registration_number
        self.user_id = user_id

    def __str__(self):
        return self.registration_number

class Teacher:
    def __init__(self, user_id, id=None):
        self.id = id
        self.user_id = user_id

    def __str__(self):
        return str(self.id)

class Subject:
    def __init__(self, name, teacher_id, id=None):
        self.id = id
        self.name = name
        self.teacher_id = teacher_id

    def __str__(self):
        return self.name

class StudentSubject:
    def __init__(self, student_id, subject_id):
        self.student_id = student_id
        self.subject_id = subject_id

class AppointmentStatus:
    def __init__(self, name, id=None):
        self.id = id
        self.name = name

    def __str__(self):
        return self.name

class Appointment:
    def __init__(self, description, scheduled_at, appointments_status_id, subject_id, teacher_id=None, student_id=None, notes=None, created_at=None, updated_at=None, id=None):
        self.id = id
        self.description = description
        self.scheduled_at = scheduled_at
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
        self.appointments_status_id = appointments_status_id
        self.subject_id = subject_id
        self.teacher_id = teacher_id
        self.student_id = student_id

    def __str__(self):
        return str(self.scheduled_at)