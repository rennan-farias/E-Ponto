from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
import requests
import random
import string
from datetime import datetime, timedelta



# Inicialização do Flask
app = Flask(__name__)

# Definindo a chave secreta para o Flask
app.secret_key = os.urandom(24)  # Gerando uma chave secreta aleatória para o Flask

# Configuração do banco de dados (utilizando SQLite como exemplo)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'  # Caminho para o banco de dados
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração do Flask-Mail para envio de e-mails
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Servidor SMTP para Gmail
app.config['MAIL_PORT'] = 587  # Porta para envio de e-mail
app.config['MAIL_USE_TLS'] = True  # TLS (Segurança)
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # Substitua pelo seu e-mail
app.config['MAIL_PASSWORD'] = 'sua_senha_de_aplicativo'  # Substitua pela senha de aplicativo (não a senha do Gmail)
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'  # E-mail de envio

# Inicializando o banco de dados e Flask-Mail
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

class TokenRecuperacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_usuario = db.Column(db.String(120), db.ForeignKey('usuario.email'), nullable=False)
    token = db.Column(db.String(120), unique=True, nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_expiracao = db.Column(db.DateTime, nullable=False)

# Método para verificar se o token está expirado
def is_expirado(self):
    return datetime.utcnow() > self.data_expiracao

# Modelo de Usuário (tabela de usuários no banco)
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    professor = db.Column(db.String(120), nullable=True)
    matricula = db.Column(db.String(80), unique=True, nullable=False)
    endereco_estagio = db.Column(db.String(200), nullable=False)
    periodo = db.Column(db.String(20), nullable=False)
    turma = db.Column(db.String(20), nullable=False)
    curso = db.Column(db.String(120), nullable=False)
    turno = db.Column(db.String(20), nullable=False)

# Modelo para registrar ponto
class RegistroPonto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricula_usuario = db.Column(db.String(80), db.ForeignKey('usuario.matricula'), nullable=False)
    data_hora = db.Column(db.String(120), nullable=False)
    localizacao = db.Column(db.String(200), nullable=False)



@app.route('/esqueci-minha-senha', methods=['GET', 'POST'])
def esqueci_minha_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Verificar se o e-mail existe no banco de dados
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            # Gerar um token de recuperação temporário
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
            # Definir a data de expiração para 1 hora a partir da criação
            data_expiracao = datetime.utcnow() + timedelta(hours=1)
            
            # Armazenar o token no banco de dados
            novo_token = TokenRecuperacao(
                email_usuario=email,
                token=token,
                data_expiracao=data_expiracao
            )
            db.session.add(novo_token)
            db.session.commit()

            # Enviar e-mail com o token de recuperação
            link_redefinicao = url_for('redefinir_senha', token=token, _external=True)
            msg = Message(
                'Recuperação de Senha',
                recipients=[email]
            )
            msg.body = f'Olá, {usuario.nome}. Clique no link abaixo para redefinir sua senha:\n\n'
            msg.body += f'{link_redefinicao}'
            
            try:
                mail.send(msg)
                flash('Instruções para recuperação de senha foram enviadas para o seu e-mail.', 'success')
            except Exception as e:
                flash(f'Erro ao enviar o e-mail: {str(e)}', 'error')
        else:
            flash('E-mail não encontrado.', 'error')
        
        return redirect(url_for('esqueci_minha_senha'))
    
    return render_template('esqueci_minha_senha.html')

@app.route('/obter-endereco', methods=['POST'])
def obter_endereco():
    lat = request.json.get('lat')
    lng = request.json.get('lng')

    # Usando a chave da API do OpenCage
    api_key = os.getenv('OPENCAGE_API_KEY', '3c71999bc3074a27bb65fd144f12a2bf')  # Substitua pela sua chave da API

    if not api_key:
        return jsonify({'error': 'Chave da API não configurada'}), 500

    # Construir a URL para fazer a requisição
    url = f'https://api.opencagedata.com/geocode/v1/json?q={lat}+{lng}&key={api_key}'

    try:
        response = requests.get(url)
        response.raise_for_status()  # Verifica se houve erro na requisição
        data = response.json()

        # Verifica se a resposta contém resultados
        if data['status']['code'] == 200 and data['results']:
            endereco = data['results'][0]['formatted']
            return jsonify({'endereco': endereco})
        else:
            print(f"Erro na resposta da API: {data}")  # Log de erro
            return jsonify({'error': 'Endereço não encontrado'}), 400

    except requests.RequestException as e:
        print(f'Erro na requisição: {e}')  # Log de erro
        return jsonify({'error': 'Erro ao fazer a requisição'}), 500

# Rota para cadastro de usuário
@app.route('/cadastrar-usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        # Obtendo dados do formulário
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        professor = request.form['professor']
        matricula = request.form['matricula']
        endereco_estagio = request.form['endereco_estagio']
        periodo = request.form['periodo']
        turma = request.form['turma']
        curso = request.form['curso']
        turno = request.form['turno']

        # Verificar se a matrícula ou e-mail já existe no banco de dados
        usuario_existente = Usuario.query.filter(
            (Usuario.matricula == matricula) | (Usuario.email == email)
        ).first()
        if usuario_existente:
            flash('Usuário já cadastrado!')
            return redirect(url_for('cadastrar_usuario'))

        # Criando um novo usuário no banco de dados
        novo_usuario = Usuario(
            nome=nome, email=email, senha=senha, professor=professor,
            matricula=matricula, endereco_estagio=endereco_estagio,
            periodo=periodo, turma=turma, curso=curso, turno=turno
        )
        db.session.add(novo_usuario)
        db.session.commit()

        flash('Usuário cadastrado com sucesso!')
        return redirect(url_for('login'))

    return render_template('cadastrar_usuario.html')

# Rota para login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']
        session['matricula'] = matricula

        # Verifica se a matrícula e a senha estão corretas no banco de dados
        usuario = Usuario.query.filter_by(matricula=matricula).first()
        if usuario and usuario.senha == senha:
            return redirect(url_for('registrar_ponto', matricula=matricula))
        else:
            flash('Matrícula ou senha incorreta.')
            return redirect(url_for('login'))

    return render_template('index.html')

# Rota para registrar ponto de presença
@app.route('/registrar-ponto/<matricula>', methods=['GET', 'POST'])
def registrar_ponto(matricula):
    if request.method == 'POST':
        data_hora = request.form.get('data_hora')
        localizacao = request.form.get('localizacao')

        # Verifica se a matrícula do usuário existe
        usuario = Usuario.query.filter_by(matricula=matricula).first()
        if usuario:
            # Criando um novo registro de ponto no banco de dados
            novo_registro = RegistroPonto(
                matricula_usuario=matricula, data_hora=data_hora, localizacao=localizacao
            )
            db.session.add(novo_registro)
            db.session.commit()
            flash('Ponto registrado com sucesso!')
        else:
            flash('Usuário não encontrado.')
        
        return redirect(url_for('registrar_ponto', matricula=matricula))

    return render_template('registrar_ponto.html', matricula=matricula)

@app.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    # Verificar se o token é válido
    token_recuperacao = TokenRecuperacao.query.filter_by(token=token).first()
    
    if not token_recuperacao:
        flash('Token inválido ou expirado.', 'error')
        return redirect(url_for('login'))
    
    if token_recuperacao.is_expirado():
        flash('Token expirado. Solicite uma nova recuperação de senha.', 'error')
        return redirect(url_for('esqueci_minha_senha'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        # Aqui você pode adicionar validações para a senha, como comprimento mínimo ou complexidade
        
        # Encontrar o usuário pelo e-mail do token
        usuario = Usuario.query.filter_by(email=token_recuperacao.email_usuario).first()
        if usuario:
            usuario.senha = nova_senha  # Atualizar a senha
            db.session.commit()
            # Remover o token após a utilização
            db.session.delete(token_recuperacao)
            db.session.commit()

            flash('Senha redefinida com sucesso!', 'success')
            return redirect(url_for('login'))
    
    return render_template('redefinir_senha.html', token=token)

# Rota da Página Inicial
@app.route("/")
def index():
    return render_template("index.html")

# 1. Painel Administrativo
@app.route("/painel-admin")
def painel_admin():
    return render_template("painel_admin.html")

# 2. Relatórios
@app.route("/relatorios")
def relatorios():
    return render_template("relatorios.html")

# 3. Configurações de Perfil
@app.route("/configuracoes-perfil", methods=["GET", "POST"])
def configuracoes_perfil():
    if request.method == "POST":
        # Aqui você pode processar a atualização do perfil
        nome = request.form.get("nome")
        email = request.form.get("email")
        # Faça algo com essas informações (salvar no banco, por exemplo)
        return "Informações atualizadas com sucesso!"
    return render_template("configuracoes_perfil.html")

# 4. Histórico de Pontos
@app.route("/historico-pontos")
def historico_pontos():
    matricula = session.get('matricula')
    if not matricula:
        return "Usuário não autenticado", 401
    # Buscar registros de ponto para o usuário com a matrícula fornecida
    registros = RegistroPonto.query.filter_by(matricula_usuario=matricula).all()

    # Formatar os dados para serem exibidos no template
    historico = [
        {
            "data": datetime.strptime(registro.data_hora, "%d/%m/%Y %H:%M:%S").strftime("%d/%m/%Y"),
            "horario": datetime.strptime(registro.data_hora, "%d/%m/%Y %H:%M:%S").strftime("%H:%M"),
            "local": registro.localizacao
        }
        for registro in registros
    ]

    return render_template("historico_pontos.html", historico=historico)
# 5. Tela de Erro 404
@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)

