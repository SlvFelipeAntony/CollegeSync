from model import User

# SQLs ajustados para a tabela collegesync.users
SQL_SELECT_BY_EMAIL = 'SELECT * FROM collegesync.users WHERE email = %s'
SQL_SELECT_BY_ID = 'SELECT * FROM collegesync.users WHERE id = %s'
SQL_INSERT_USER = 'INSERT INTO collegesync.users (name, email, birth_date, hash_password) VALUES (%s, %s, %s, %s)'
SQL_UPDATE_USER = 'UPDATE collegesync.users SET name=%s, email=%s, birth_date=%s, hash_password=%s, updated_at=NOW() WHERE id=%s'
SQL_DELETE_USER = 'DELETE FROM collegesync.users WHERE id = %s'
SQL_INSERT_STUDENT = 'INSERT INTO collegesync.students (registration_number, user_id) VALUES (%s, %s)'
SQL_INSERT_TEACHER = 'INSERT INTO collegesync.teachers (user_id) VALUES (%s)'

SQL_PROMOTE_ADMIN = "INSERT INTO collegesync.admins (user_id) VALUES (%s)"
SQL_REVOKE_ADMIN = "DELETE FROM collegesync.admins WHERE user_id = %s"

# Lista usuários com uma flag dizendo se é admin ou não
SQL_LIST_WITH_ROLES = """
        SELECT u.id, u.name, u.email, 
               CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END as is_admin
        FROM collegesync.users u
        LEFT JOIN collegesync.admins a ON u.id = a.user_id
        ORDER BY u.name
    """

class UserDao:
    def __init__(self, db):
        self.__db = db

    def salvar(self, user):
        cursor = self.__db.connection.cursor()

        if user.id:  # Atualizar
            cursor.execute(SQL_UPDATE_USER, (user.name, user.email, user.birth_date, user.hash_password, user.id))
        else:  # Inserir novo
            cursor.execute(SQL_INSERT_USER, (user.name, user.email, user.birth_date, user.hash_password))
            user.id = cursor.lastrowid

        self.__db.connection.commit()
        return user

    def buscar_por_email(self, email):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_SELECT_BY_EMAIL, (email,))
        tupla = cursor.fetchone()
        if tupla:
            return self.__traduz_user(tupla)
        return None

    # ... métodos anteriores (salvar, buscar_por_email, etc) ...
    def buscar_perfil(self, user_id):
        cursor = self.__db.connection.cursor()

        # 1. Tenta achar na tabela ADMINS (NOVO)
        sql_admin = "SELECT id FROM collegesync.admins WHERE user_id = %s"
        cursor.execute(sql_admin, (user_id,))
        admin = cursor.fetchone()
        if admin:
            # Retornamos 'admin'
            return {'tipo': 'admin', 'id_especifico': admin[0]}

        # 2. Tenta achar na tabela de ALUNOS
        sql_aluno = "SELECT id FROM collegesync.students WHERE user_id = %s"
        cursor.execute(sql_aluno, (user_id,))
        aluno = cursor.fetchone()
        if aluno:
            return {'tipo': 'student', 'id_especifico': aluno[0]}

        # 3. Tenta achar na tabela de PROFESSORES
        sql_prof = "SELECT id FROM collegesync.teachers WHERE user_id = %s"
        cursor.execute(sql_prof, (user_id,))
        prof = cursor.fetchone()
        if prof:
            return {'tipo': 'teacher', 'id_especifico': prof[0]}

        return {'tipo': 'user', 'id_especifico': user_id}

    def salvar_perfil(self, user_id, user_type, registration_number=None):
        cursor = self.__db.connection.cursor()

        if user_type == 'student':
            if not registration_number:
                registration_number = f"TEMP{user_id}"  # Garante uma matrícula se vazio
            cursor.execute(SQL_INSERT_STUDENT, (registration_number, user_id))

        elif user_type == 'teacher':
            cursor.execute(SQL_INSERT_TEACHER, (user_id,))

        self.__db.connection.commit()

    def listar_por_id(self, id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_SELECT_BY_ID, (id,))
        tupla = cursor.fetchone()
        if tupla:
            return self.__traduz_user(tupla)
        return None

    # Traduz a tupla do banco (id, name, email, birth, pass, created, updated) para Objeto
    def __traduz_user(self, tupla):
        # tupla[0]=id, [1]=name, [2]=email, [3]=birth_date, [4]=password, [5]=created_at, [6]=updated_at
        return User(
            id=tupla[0],
            name=tupla[1],
            email=tupla[2],
            birth_date=tupla[3],
            hash_password=tupla[4],
            created_at=tupla[5],
            updated_at=tupla[6]
        )

    def listar_com_status_admin(self):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_LIST_WITH_ROLES)
        lista = []
        for row in cursor.fetchall():
            lista.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'is_admin': (row[3] == 1)
            })
        return lista

    def promover_a_admin(self, user_id):
        cursor = self.__db.connection.cursor()
        try:
            cursor.execute(SQL_PROMOTE_ADMIN, (user_id,))
            self.__db.connection.commit()
            return True
        except:
            return False  # Provavelmente já é admin

    def revogar_admin(self, user_id):
        cursor = self.__db.connection.cursor()
        cursor.execute(SQL_REVOKE_ADMIN, (user_id,))
        self.__db.connection.commit()