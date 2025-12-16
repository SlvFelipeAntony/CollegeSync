from model import Subject

class SubjectDao:
    def __init__(self, db):
        self.__db = db

    # Lista matérias com o nome do professor para exibir na tabela
    def listar(self):
        cursor = self.__db.connection.cursor()
        sql = """
            SELECT s.id, s.name, u.name as nome_prof 
            FROM collegesync.subjects s
            JOIN collegesync.teachers t ON s.teacher_id = t.id
            JOIN collegesync.users u ON t.user_id = u.id
            ORDER BY s.name
        """
        cursor.execute(sql)
        lista = []
        for row in cursor.fetchall():
            # row: 0=id, 1=nome_materia, 2=nome_professor
            lista.append({'id': row[0], 'name': row[1], 'professor': row[2]})
        return lista

    # Lista apenas professores para preencher o <select> do formulário
    def listar_professores(self):
        cursor = self.__db.connection.cursor()
        sql = """
            SELECT t.id, u.name 
            FROM collegesync.teachers t
            JOIN collegesync.users u ON t.user_id = u.id
            ORDER BY u.name
        """
        cursor.execute(sql)
        return cursor.fetchall() # Retorna tuplas (id, nome)

    def buscar_por_id(self, id):
        cursor = self.__db.connection.cursor()
        cursor.execute("SELECT * FROM collegesync.subjects WHERE id = %s", (id,))
        tupla = cursor.fetchone()
        if tupla:
            return Subject(tupla[1], tupla[2], tupla[0])
        return None

    def salvar(self, subject):
        cursor = self.__db.connection.cursor()
        if subject.id:
            cursor.execute("UPDATE collegesync.subjects SET name=%s, teacher_id=%s WHERE id=%s",
                           (subject.name, subject.teacher_id, subject.id))
        else:
            cursor.execute("INSERT INTO collegesync.subjects (name, teacher_id) VALUES (%s, %s)",
                           (subject.name, subject.teacher_id))
            subject.id = cursor.lastrowid
        self.__db.connection.commit()
        return subject

    def deletar(self, id):
        cursor = self.__db.connection.cursor()
        cursor.execute("DELETE FROM collegesync.subjects WHERE id = %s", (id,))
        self.__db.connection.commit()