from model import Appointment, Subject

# --- SQL Constants ---
SQL_LIST_SUBJECTS = "SELECT id, name, teacher_id FROM collegesync.subjects"
SQL_LIST_TEACHER_SUBJECTS = "SELECT id, name, teacher_id FROM collegesync.subjects WHERE teacher_id = %s"
SQL_FIND_TEACHER_BY_SUBJECT = "SELECT teacher_id FROM collegesync.subjects WHERE id = %s"

SQL_INSERT_APPOINTMENT = """
    INSERT INTO collegesync.appointments 
    (description, scheduled_at, notes, appointments_status_id, subject_id, teacher_id, student_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

SQL_SELECT_BY_ID = "SELECT * FROM collegesync.appointments WHERE id = %s"

SQL_UPDATE_APPOINTMENT = """
    UPDATE collegesync.appointments 
    SET description=%s, scheduled_at=%s, subject_id=%s, notes=%s
    WHERE id=%s
"""

SQL_DELETE_APPOINTMENT = "DELETE FROM collegesync.appointments WHERE id = %s"

# --- SQLs DE VISIBILIDADE DO CALENDÁRIO ---
SQL_SELECT_SHARED_STUDENT = """
    SELECT DISTINCT a.id, a.description, a.scheduled_at, s.name, a.student_id
    FROM collegesync.appointments a
    JOIN collegesync.subjects s ON a.subject_id = s.id
    LEFT JOIN collegesync.students_subjects ss ON s.id = ss.subject_id
    WHERE ss.student_id = %s OR a.student_id = %s
"""

SQL_SELECT_SHARED_TEACHER = """
    SELECT a.id, a.description, a.scheduled_at, s.name, a.student_id
    FROM collegesync.appointments a
    JOIN collegesync.subjects s ON a.subject_id = s.id
    WHERE s.teacher_id = %s
"""

SQL_SELECT_ALL_ADMIN = """
    SELECT a.id, a.description, a.scheduled_at, s.name, u.name as nome_aluno
    FROM collegesync.appointments a
    JOIN collegesync.subjects s ON a.subject_id = s.id
    LEFT JOIN collegesync.students st ON a.student_id = st.id
    LEFT JOIN collegesync.users u ON st.user_id = u.id
"""

# --- SQLs DE DETALHES E LISTAGENS ESPECÍFICAS ---
SQL_SELECT_DETAILS = """
    SELECT a.id, a.description, a.scheduled_at, a.notes, 
           s.name as materia, u.name as nome_aluno, t_u.name as nome_professor,
           a.student_id, st.name as status_nome, a.teacher_id
    FROM collegesync.appointments a
    JOIN collegesync.subjects s ON a.subject_id = s.id
    LEFT JOIN collegesync.students stu ON a.student_id = stu.id
    LEFT JOIN collegesync.users u ON stu.user_id = u.id
    JOIN collegesync.teachers t ON s.teacher_id = t.id
    JOIN collegesync.users t_u ON t.user_id = t_u.id
    JOIN collegesync.appointments_status st ON a.appointments_status_id = st.id
    WHERE a.id = %s
"""

SQL_SELECT_MY_SUBJECTS = """
    SELECT s.name, u.name 
    FROM collegesync.subjects s
    JOIN collegesync.students_subjects ss ON s.id = ss.subject_id
    JOIN collegesync.teachers t ON s.teacher_id = t.id
    JOIN collegesync.users u ON t.user_id = u.id
    WHERE ss.student_id = %s
"""

SQL_SELECT_MY_STUDENTS = """
    SELECT u.name, u.email, st.registration_number, s.name
    FROM collegesync.subjects s
    JOIN collegesync.students_subjects ss ON s.id = ss.subject_id
    JOIN collegesync.students st ON ss.student_id = st.id
    JOIN collegesync.users u ON st.user_id = u.id
    WHERE s.teacher_id = %s
    ORDER BY s.name, u.name
"""


class AppointmentDao:
    def __init__(self, db):
        self.__db = db

    # 1. Combos de Matérias
    def listar_materias(self):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_LIST_SUBJECTS)
        materias = []
        for row in cursor.fetchall():
            materias.append(Subject(id=row[0], name=row[1], teacher_id=row[2]))
        return materias

    def listar_materias_do_professor_combo(self, teacher_id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_LIST_TEACHER_SUBJECTS, (teacher_id,))
        materias = []
        for row in cursor.fetchall():
            materias.append(Subject(id=row[0], name=row[1], teacher_id=row[2]))
        return materias

    # 2. Helpers
    def buscar_professor_da_materia(self, subject_id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_FIND_TEACHER_BY_SUBJECT, (subject_id,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None

    # 3. CRUD Agendamento
    def salvar(self, appt):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_INSERT_APPOINTMENT, (
            appt.description, appt.scheduled_at, appt.notes,
            1, appt.subject_id, appt.teacher_id, appt.student_id
        ))
        self.__db.connection.commit()
        return cursor.lastrowid

    def buscar_por_id(self, id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_SELECT_BY_ID, (id,))
        tupla = cursor.fetchone()
        if tupla:
            return Appointment(
                id=tupla[0], description=tupla[1], scheduled_at=tupla[2], notes=tupla[3],
                appointments_status_id=tupla[6], subject_id=tupla[7],
                teacher_id=tupla[8], student_id=tupla[9]
            )
        return None

    def buscar_detalhes(self, id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_SELECT_DETAILS, (id,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'description': row[1],
                'scheduled_at': row[2],
                'notes': row[3],
                'materia': row[4],
                'aluno': row[5] if row[5] else "Professor",
                'professor': row[6],
                'student_id': row[7],
                'status': row[8],
                'teacher_id': row[9]
            }
        return None

    def atualizar(self, appt):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_UPDATE_APPOINTMENT, (
            appt.description, appt.scheduled_at, appt.subject_id, appt.notes, appt.id
        ))
        self.__db.connection.commit()

    def excluir(self, id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_DELETE_APPOINTMENT, (id,))
        self.__db.connection.commit()

    # 4. CALENDÁRIO (A Lógica Principal)
    def listar_para_calendario(self, perfil_id, tipo_usuario):
        cursor = self.__db.connection.cursor()

        # ADMIN: Vê tudo
        if tipo_usuario == 'admin':
            cursor.execute(SQL_SELECT_ALL_ADMIN)
            eventos = []
            for row in cursor.fetchall():
                eventos.append({
                    'id': row[0],
                    'title': f"[Admin] {row[3]} - {row[4]}",
                    'start': str(row[2]),
                    'color': '#dc3545'
                })
            return eventos

        # ALUNO
        elif tipo_usuario == 'student':
            cursor.execute(SQL_SELECT_SHARED_STUDENT, (perfil_id, perfil_id))
            cor_padrao = '#0d6efd'

            # PROFESSOR
        else:
            cursor.execute(SQL_SELECT_SHARED_TEACHER, (perfil_id,))
            cor_padrao = '#198754'

        eventos = []
        for row in cursor.fetchall():
            sou_dono = False
            if tipo_usuario == 'student' and row[4] == perfil_id:
                sou_dono = True

            titulo = f"{row[3]} - {row[1]}"
            cor = cor_padrao

            if tipo_usuario == 'student' and not sou_dono:
                cor = '#6c757d'
                titulo = f"(Colega) {row[3]}"

            eventos.append({
                'id': row[0],
                'title': titulo,
                'start': str(row[2]),
                'color': cor
            })

        return eventos

    # 5. Listagens Específicas (ESTAVAM FALTANDO)
    def listar_materias_do_aluno(self, student_id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_SELECT_MY_SUBJECTS, (student_id,))
        materias = []
        for row in cursor.fetchall():
            materias.append({'materia': row[0], 'professor': row[1]})
        return materias

    def listar_alunos_do_professor(self, teacher_id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_SELECT_MY_STUDENTS, (teacher_id,))
        alunos = []
        for row in cursor.fetchall():
            alunos.append({
                'nome': row[0],
                'email': row[1],
                'matricula': row[2],
                'materia': row[3]
            })
        return alunos