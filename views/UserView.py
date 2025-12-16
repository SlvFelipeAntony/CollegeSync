from flask import render_template, request, redirect, session, flash, url_for
from model import User
from dao.UserDao import UserDao
from MySQLdb import IntegrityError # Importante para capturar o erro do banco
from dao.AppointmentDao import AppointmentDao
from datetime import datetime


def init_user_routes(app, db, bcrypt):  # Adicionei bcrypt como parametro
    dao = UserDao(db)

    @app.route('/')
    def index():
        # Se não estiver logado, manda pro login
        if 'usuario_logado' not in session or session['usuario_logado'] is None:
            return redirect(url_for('login'))

        # Se estiver logado, carrega a AGENDA (Calendário)
        return render_template('appointment/calendar.html', titulo='Minha Agenda')

    # --- ROTA DE EXIBIR O LOGIN (Faltava esta!) ---
    @app.route('/login')
    def login():
        return render_template('user/login.html')

    @app.route('/autenticar', methods=['POST'])
    def autenticar():
        email = request.form['email']
        senha = request.form['password']

        user = dao.buscar_por_email(email)  # Busca na tabela users

        if user and bcrypt.check_password_hash(user.hash_password, senha):
            # 1. Identifica se é Aluno ou Professor
            perfil = dao.buscar_perfil(user.id)

            # 2. Salva na sessão
            session['usuario_logado'] = user.id  # ID da tabela users (login)
            session['usuario_nome'] = user.name
            session['usuario_tipo'] = perfil['tipo']  # 'student' ou 'teacher'
            session['perfil_id'] = perfil['id_especifico']  # ID de aluno ou professor (para usar nos agendamentos)

            flash(f'Bem-vindo, {user.name} ({perfil["tipo"]})!')
            return redirect(url_for('index'))  # Mudei para index para testar o home

        flash('Usuário ou senha inválidos.')
        return redirect(url_for('login'))

    @app.route('/logout')
    def logout():
        session['usuario_logado'] = None
        session.clear()
        flash('Logout efetuado com sucesso!')
        return redirect(url_for('login'))

    # --- ROTA DE CADASTRO ---
    @app.route('/registro')
    def registro():
        return render_template('user/register.html')

    @app.route('/criar', methods=['POST'])
    def criar():
        name = request.form['name']
        email = request.form['email']
        birth_date = request.form['birth_date']
        password = request.form['password']

        user_type = request.form['user_type']
        registration_number = request.form.get('registration_number')

        try:
            # 1. Tenta criar o usuário base
            hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(name, email, hash_password, birth_date=birth_date)

            # ATENÇÃO: Se o email já existir, o erro estoura aqui
            user = dao.salvar(user)

            # 2. Tenta vincular ao perfil
            # ATENÇÃO: Se a matrícula já existir, o erro estoura aqui
            dao.salvar_perfil(user.id, user_type, registration_number)

            flash('Cadastro realizado com sucesso! Faça login.')
            return redirect(url_for('login'))

        except IntegrityError as e:
            # O banco retornou um erro de integridade (duplicidade)
            erro_str = str(e)

            # Verificamos se foi o email ou a matrícula
            if 'email' in erro_str:
                flash('Erro: Este email já está cadastrado.')
            elif 'registration_number' in erro_str:
                flash('Erro: Esta matrícula já está cadastrada.')
            else:
                flash('Erro: Dados duplicados no sistema.')

            return redirect(url_for('registro'))

        except Exception as e:
            # Qualquer outro erro genérico
            flash(f'Ocorreu um erro inesperado: {str(e)}')
            return redirect(url_for('registro'))

    @app.route('/minhas-materias')
    def my_subjects():
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        # Só alunos podem acessar
        if session['usuario_tipo'] != 'student':
            flash('Acesso restrito a alunos.')
            return redirect(url_for('index'))

        # Instancia o DAO (pois estamos no UserView e ele não foi instanciado aqui por padrão)
        appt_dao = AppointmentDao(db)

        materias = appt_dao.listar_materias_do_aluno(session['perfil_id'])

        return render_template('user/subjects.html', materias=materias)

    @app.route('/perfil')
    def profile():
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        # Busca dados atuais do usuário para preencher o formulário
        user = dao.listar_por_id(session['usuario_logado'])

        return render_template('user/profile.html', user=user)

    # Rota para salvar alterações
    @app.route('/perfil/atualizar', methods=['POST'])
    def update_profile():
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        # Recupera o usuário original do banco
        user = dao.listar_por_id(session['usuario_logado'])

        # Atualiza os campos básicos
        user.name = request.form['name']
        user.email = request.form['email']
        user.birth_date = request.form['birth_date']

        # Lógica da Senha: Só altera se o campo não estiver vazio
        nova_senha = request.form['password']
        if nova_senha:
            user.hash_password = bcrypt.generate_password_hash(nova_senha).decode('utf-8')

        try:
            dao.salvar(user)
            # Atualiza o nome na sessão caso tenha mudado
            session['usuario_nome'] = user.name
            flash('Perfil atualizado com sucesso!')
        except Exception as e:
            flash(f'Erro ao atualizar: {str(e)}')

        return redirect(url_for('profile'))

    @app.route('/meus-alunos')
    def my_students():
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        # SEGURANÇA: Só professor entra aqui
        if session['usuario_tipo'] != 'teacher':
            flash('Acesso restrito a professores.')
            return redirect(url_for('index'))

        # Instancia o DAO
        appt_dao = AppointmentDao(db)

        # Busca usando o ID de Professor (perfil_id)
        alunos = appt_dao.listar_alunos_do_professor(session['perfil_id'])

        return render_template('user/students.html', alunos=alunos)

