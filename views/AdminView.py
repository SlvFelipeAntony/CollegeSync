from flask import render_template, request, redirect, session, flash, url_for
from dao.UserDao import UserDao
from dao.SubjectDao import SubjectDao
from model import Subject, User


def init_admin_routes(app, db):
    user_dao = UserDao(db)
    subject_dao = SubjectDao(db)

    @app.route('/admin/materias')
    def admin_subjects():
        if not admin_required(): return redirect(url_for('login'))
        materias = subject_dao.listar()
        return render_template('admin/subjects.html', materias=materias)

    @app.route('/admin/materias/nova')
    def admin_new_subject():
        if not admin_required(): return redirect(url_for('login'))
        professores = subject_dao.listar_professores()
        return render_template('admin/subject_form.html', professores=professores, subject=None)

    @app.route('/admin/materias/salvar', methods=['POST'])
    def admin_save_subject():
        if not admin_required(): return redirect(url_for('login'))

        id = request.form.get('id')  # Se tiver ID é edição, se não é criação
        name = request.form['name']
        teacher_id = request.form['teacher_id']

        sub = Subject(name, teacher_id, id if id else None)
        subject_dao.salvar(sub)

        flash('Disciplina salva com sucesso!')
        return redirect(url_for('admin_subjects'))

    @app.route('/admin/materias/editar/<int:id>')
    def admin_edit_subject(id):
        if not admin_required(): return redirect(url_for('login'))

        subject = subject_dao.buscar_por_id(id)
        professores = subject_dao.listar_professores()
        return render_template('admin/subject_form.html', professores=professores, subject=subject)

    @app.route('/admin/materias/deletar/<int:id>')
    def admin_delete_subject(id):
        if not admin_required(): return redirect(url_for('login'))
        try:
            subject_dao.deletar(id)
            flash('Disciplina removida.')
        except Exception as e:
            flash('Erro: Não é possível excluir disciplina que tem alunos ou agendamentos vinculados.')
        return redirect(url_for('admin_subjects'))

    # _____________________________________

    # Decorator ou função auxiliar para proteger rotas de admin
    def admin_required():
        if 'usuario_logado' not in session or session.get('usuario_tipo') != 'admin':
            return False
        return True

    @app.route('/admin')
    def admin_dashboard():
        if not admin_required():
            return redirect(url_for('login'))
        return render_template('admin/dashboard.html')

    # --- GERENCIAMENTO DE USUÁRIOS ---
    @app.route('/admin/usuarios')
    def admin_users():
        if not admin_required(): return redirect(url_for('login'))

        # Usa o novo método que diz quem é admin
        usuarios = user_dao.listar_com_status_admin()
        return render_template('admin/users_list.html', usuarios=usuarios)

    @app.route('/admin/usuario/deletar/<int:id>')
    def admin_delete_user(id):
        if not admin_required():
            return redirect(url_for('login'))

        # Cuidado: Ao deletar user, o banco deve ter ON DELETE CASCADE
        # nas FKs (students, teachers, appointments), senão vai dar erro.
        try:
            user_dao.deletar(id)  # Certifique-se que existe no UserDao
            flash('Usuário excluído com sucesso.')
        except Exception as e:
            flash(f'Erro ao excluir: {str(e)}')

        return redirect(url_for('admin_users'))

    @app.route('/admin/usuario/form')
    @app.route('/admin/usuario/form/<int:id>')
    def admin_user_form(id=None):
        if not admin_required(): return redirect(url_for('login'))

        user = None
        if id:
            user = user_dao.listar_por_id(id)

        return render_template('admin/user_form.html', user=user)

    @app.route('/admin/usuario/salvar', methods=['POST'])
    def admin_save_user():
        if not admin_required(): return redirect(url_for('login'))

        id = request.form.get('id')
        name = request.form['name']
        email = request.form['email']
        birth_date = request.form['birth_date']
        password = request.form['password']  # Pode vir vazio na edição

        # Lógica de Hash de Senha
        hash_password = None
        if password:
            # Se digitou senha, cria novo hash
            # OBS: Precisa do 'bcrypt' aqui. Se não tiver passado na init,
            # use 'from app import bcrypt' ou passe como parametro na init_admin_routes
            from flask_bcrypt import generate_password_hash
            hash_password = generate_password_hash(password).decode('utf-8')

        if id:  # Edição
            user = user_dao.listar_por_id(id)
            user.name = name
            user.email = email
            user.birth_date = birth_date
            if hash_password:
                user.hash_password = hash_password
            user_dao.salvar(user)
            flash('Usuário atualizado.')
        else:  # Criação
            if not password:  # Senha obrigatória na criação
                flash('Senha é obrigatória para novos usuários.')
                return redirect(url_for('admin_user_form'))

            user = User(name, email, hash_password, birth_date=birth_date)
            user_dao.salvar(user)
            flash('Usuário criado com sucesso.')

        return redirect(url_for('admin_users'))

    # --- PROMOVER / REVOGAR ADMIN ---
    @app.route('/admin/usuario/toggle-admin/<int:id>/<int:acao>')
    def admin_toggle_role(id, acao):
        if not admin_required(): return redirect(url_for('login'))

        # Evita que o admin remova a si mesmo (opcional, mas bom)
        if id == session['usuario_logado']:
            flash('Você não pode alterar seu próprio status de admin.')
            return redirect(url_for('admin_users'))

        if acao == 1:  # Promover
            user_dao.promover_a_admin(id)
            flash('Usuário agora é Administrador.')
        else:  # Revogar
            user_dao.revogar_admin(id)
            flash('Acesso de Administrador removido.')

        return redirect(url_for('admin_users'))