from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '9cfbfd3e2cd8d4d14c6b7c151ecf374e')  # Altere para sua chave secreta

# Simulação de banco de dados
usuarios = {
    '12345': 'senha123',
    '01578575': '01578575'
}

pontos_registrados = {}  # Dicionário para armazenar registros de pontos

# Endpoint para geocodificação reversa usando o backend
@app.route('/obter-endereco', methods=['POST'])
def obter_endereco():
    lat = request.json.get('lat')
    lng = request.json.get('lng')
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')  # Obtém a chave da API do ambiente

    if not api_key:
        return jsonify({'error': 'Chave da API não configurada'}), 500

    url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'OK':
            endereco = data['results'][0]['formatted_address']
            return jsonify({'endereco': endereco})
        else:
            return jsonify({'error': 'Não foi possível obter o endereço'}), 400
    except requests.RequestException as e:
        return jsonify({'error': 'Erro ao fazer a requisição'}), 500

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']

        # Verifica se a matrícula e a senha estão corretas
        if matricula in usuarios and usuarios[matricula] == senha:
            return redirect(url_for('registrar_ponto', matricula=matricula))
        else:
            flash('Matrícula ou senha incorreta.')
            return redirect(url_for('login'))

    return render_template('index.html')  # Certifique-se de que o template existe

@app.route('/esqueci-minha-senha', methods=['GET', 'POST'])
def esqueci_minha_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Simulação de verificação de e-mail e envio de instruções
        if email in usuarios:
            flash('Instruções para recuperação de senha foram enviadas para o seu e-mail.', 'success')
        else:
            flash('E-mail não encontrado.', 'error')
        
        return redirect(url_for('esqueci_minha_senha'))
    
    return render_template('esqueci_minha_senha.html')

@app.route('/cadastrar-usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        matricula = request.form['matricula']
        senha = request.form['senha']
        
        # Adiciona a nova matrícula e senha ao dicionário de usuários
        usuarios[matricula] = senha
        flash('Usuário cadastrado com sucesso!')
        return redirect(url_for('login'))

    return render_template('cadastrar_usuario.html')  # Certifique-se de que o template existe

@app.route('/registrar-ponto/<matricula>', methods=['GET', 'POST'])
def registrar_ponto(matricula):
    if request.method == 'POST':
        data_hora = request.form.get('data_hora')
        localizacao = request.form.get('localizacao')

        pontos_registrados[matricula] = {
            'data_hora': data_hora,
            'localizacao': localizacao
        }

        flash('Ponto registrado com sucesso!')
        return redirect(url_for('registrar_ponto', matricula=matricula))  # Redireciona para a mesma página após o registro

    return render_template('registrar_ponto.html', matricula=matricula)

if __name__ == '__main__':
    app.run(debug=True)
