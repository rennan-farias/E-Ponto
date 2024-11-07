from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os
import requests
import random
import string

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
mail = Mail(app)

# Modelo de Usuário (tabela de usuários no banco)
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(120), nullable=False)
    professor = db.Column(db.String(120), nullable=False)
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

# Rota para recuperação de senha
@app.route('/esqueci-minha-senha', methods=['GET', 'POST'])
def esqueci_minha_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Verificar se o e-mail existe no banco de dados
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            # Gerar um token de recuperação temporário
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

            # Enviar e-mail com o token de recuperação
            msg = Message(
                'Recuperação de Senha',
                recipients=[email]
            )
            msg.body = f'Olá, {usuario.nome}. Clique no link abaixo para redefinir sua senha:\n\n'
            msg.body += f'http://127.0.0.1:5000/redefinir-senha/{token}'
            try:
                mail.send(msg)
                flash('Instruções para recuperação de senha foram enviadas para o seu e-mail.', 'success')
            except Exception as e:
                flash(f'Erro ao enviar o e-mail: {str(e)}', 'error')
        else:
            flash('E-mail não encontrado.', 'error')
        
        return redirect(url_for('esqueci_minha_senha'))
    
    return render_template('esqueci_minha_senha.html')

# Criar o banco de dados antes de iniciar o servidor
with app.app_context():
    db.create_all()

# Iniciando a aplicação Flask
if __name__ == '__main__':
    app.run(debug=True)
