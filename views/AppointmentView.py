from flask import render_template, request, redirect, session, flash, url_for, jsonify
from model import Appointment
from dao.AppointmentDao import AppointmentDao


def init_appointment_routes(app, db):
    dao = AppointmentDao(db)

    # --- 1. ROTA DE CRIAÇÃO (Para garantir que você tem) ---
    @app.route('/agendamento/novo')
    def new_appointment():
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        # Lógica inteligente para o <select> de matérias
        if session['usuario_tipo'] == 'teacher':
            # Se for professor, só mostra as matérias DELE
            materias = dao.listar_materias_do_professor_combo(session['perfil_id'])
        else:
            # Se for aluno, mostra todas (ou as que ele cursa, dependendo da sua regra)
            materias = dao.listar_materias()

        return render_template('appointment/new.html', materias=materias)

    @app.route('/agendamento/criar', methods=['POST'])
    def create_appointment():
        description = request.form['description']
        scheduled_at = request.form['scheduled_at']
        subject_id = request.form['subject_id']
        notes = request.form['notes']

        # Se for aluno, pega o ID. Se for professor, student_id fica None (NULL no banco)
        if session['usuario_tipo'] == 'student':
            student_id = session.get('perfil_id')
        else:
            student_id = None

        teacher_id = dao.buscar_professor_da_materia(subject_id)

        appt = Appointment(
            description=description, scheduled_at=scheduled_at, appointments_status_id=1,
            subject_id=subject_id, teacher_id=teacher_id, student_id=student_id, notes=notes
        )
        dao.salvar(appt)
        flash('Agendamento criado!')
        return redirect(url_for('index'))

    @app.route('/agendamento/detalhes/<int:id>')
    def view_appointment(id):
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        detalhes = dao.buscar_detalhes(id)

        if not detalhes:
            flash('Agendamento não encontrado.')
            return redirect(url_for('index'))

        # --- NOVA LÓGICA DE PERMISSÃO ---
        pode_editar = False

        # 1. É o aluno dono do agendamento?
        if session['usuario_tipo'] == 'student' and detalhes['student_id'] == session.get('perfil_id'):
            pode_editar = True

        # 2. É o professor dessa matéria?
        # (Verifica se sou teacher E se o teacher_id do agendamento é o meu)
        if session['usuario_tipo'] == 'teacher' and detalhes['teacher_id'] == session.get('perfil_id'):
            pode_editar = True

        # 3. É ADMIN? (LIBERA TUDO)
        if session['usuario_tipo'] == 'admin':
            pode_editar = True

        return render_template('appointment/view.html', appt=detalhes, pode_editar=pode_editar)

    @app.route('/agendamento/editar/<int:id>')
    def edit_appointment(id):
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        # 1. Busca os detalhes para saber quem são os donos
        # (Usamos buscar_detalhes para ter acesso fácil aos IDs)
        detalhes = dao.buscar_detalhes(id)

        if not detalhes:
            flash('Agendamento não encontrado.')
            return redirect(url_for('index'))

        # 2. VERIFICAÇÃO DE SEGURANÇA (A mesma do view_appointment)
        eh_aluno_dono = (session['usuario_tipo'] == 'student' and detalhes['student_id'] == session.get('perfil_id'))
        eh_prof_da_materia = (session['usuario_tipo'] == 'teacher' and detalhes['teacher_id'] == session.get('perfil_id'))

        if not (eh_aluno_dono or eh_prof_da_materia or session['usuario_tipo'] == 'admin'):
            flash('Você não tem permissão para editar este agendamento.')
            return redirect(url_for('index'))

        # 3. Carrega a lista de matérias para o <select>
        # Se for professor, carrega as matérias dele. Se for aluno, carrega todas.
        if session['usuario_tipo'] == 'teacher' or session['usuario_tipo'] == 'admin':
            materias = dao.listar_materias_do_professor_combo(session['perfil_id'])
        else:
            materias = dao.listar_materias()

        # Transformamos o dicionário 'detalhes' de volta num objeto Appointment
        # ou passamos o dicionário direto pro template.
        # O template edit.html espera um objeto 'appt' com atributos .description, etc.
        # Para facilitar, vamos passar o dicionário 'detalhes' e ajustar o HTML se precisar,
        # mas como seu DAO retorna objeto no buscar_por_id, vamos usar ele para manter compatibilidade com o template:
        appt = dao.buscar_por_id(id)

        return render_template('appointment/edit.html', appt=appt, materias=materias)

    @app.route('/agendamento/atualizar', methods=['POST'])
    def update_appointment():
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        id = request.form['id']
        appt = dao.buscar_por_id(id)

        # REPETIR SEGURANÇA NO POST (Sempre valide no servidor!)
        eh_aluno_dono = (session['usuario_tipo'] == 'student' and appt.student_id == session.get('perfil_id'))
        eh_prof_da_materia = (session['usuario_tipo'] == 'teacher' and appt.teacher_id == session.get('perfil_id'))

        if not (eh_aluno_dono or eh_prof_da_materia or session['usuario_tipo'] == 'admin'):
            flash('Permissão negada.')
            return redirect(url_for('index'))

        # Atualiza os dados
        appt.description = request.form['description']
        appt.scheduled_at = request.form['scheduled_at']
        appt.subject_id = request.form['subject_id']
        appt.notes = request.form['notes']

        # Se você tiver campo de status no form de edição, atualize aqui também
        # appt.appointments_status_id = request.form['status']

        dao.atualizar(appt)
        flash('Agendamento atualizado com sucesso!')
        return redirect(url_for('index'))

    @app.route('/agendamento/deletar/<int:id>')
    def delete_appointment(id):
        if 'usuario_logado' not in session:
            return redirect(url_for('login'))

        appt = dao.buscar_por_id(id)

        # Segurança
        if appt.student_id != session.get('perfil_id') and session['usuario_tipo'] != 'admin':
            flash('Você não pode excluir agendamentos de outros.')
            return redirect(url_for('index'))

        dao.excluir(id)
        flash('Agendamento excluído.')
        return redirect(url_for('index'))

    # ... (manter get_appointments_json igual, pois já mudamos a DAO) ...
    @app.route('/agendamento/dados')
    def get_appointments_json():
        # Admin pode não ter 'perfil_id' se não estiver nas tabelas de aluno/prof,
        # mas precisa ter 'usuario_tipo' == 'admin'
        if 'usuario_logado' not in session:
            return jsonify([])

        perfil_id = session.get('perfil_id')
        tipo = session['usuario_tipo']  # Aqui deve vir 'admin', 'student' ou 'teacher'

        eventos = dao.listar_para_calendario(perfil_id, tipo)
        return jsonify(eventos)
