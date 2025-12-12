import os
import json
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_socketio import SocketIO, emit

# --- CONFIGURAÇÕES E ARQUIVOS ---
basedir = os.path.abspath(os.path.dirname(__file__))
USERS_FILE = os.path.join(basedir, 'users.json') 
FLASHCARDS_FILE = os.path.join(basedir, 'flashcards.json')
CONTENT_FILE = os.path.join(basedir, 'content.json')
ROTATION_FILE = os.path.join(basedir, 'rotation.json')

# --- PERSISTÊNCIA (JSON) ---
def load_users():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_users(users_data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        data_to_save = {str(k): v for k, v in users_data.items()}
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# --- LÓGICA DE CONTEÚDO (IMERSÃO) ---
class ConteudoImersao:
    def __init__(self, titulo, tipo, texto_original, traducao):
        self.titulo = titulo
        self.tipo = tipo 
        self.texto_original = texto_original
        self.traducao = traducao

def carregar_conteudos():
    try:
        if os.path.exists(CONTENT_FILE):
            with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
                return [ConteudoImersao(**d) for d in json.load(f)]
    except: pass
    return []

def obter_conteudo_semanal(todos_conteudos):
    """Retorna 2 textos, atualizando a cada 7 dias."""
    if not todos_conteudos: return []
    
    estado = {}
    # Carrega estado anterior
    if os.path.exists(ROTATION_FILE):
        try:
            with open(ROTATION_FILE, 'r') as f:
                estado = json.load(f)
        except: pass
    
    last_update_str = estado.get('last_update', '2000-01-01')
    current_index = estado.get('current_index', 0)
    
    last_update = datetime.strptime(last_update_str, '%Y-%m-%d')
    agora = datetime.now()
    
    # Verifica se passou 7 dias
    if (agora - last_update).days >= 7:
        current_index = (current_index + 2) % len(todos_conteudos)
        with open(ROTATION_FILE, 'w') as f:
            json.dump({
                'last_update': agora.strftime('%Y-%m-%d'),
                'current_index': current_index
            }, f)
            
    # Seleciona 2 itens 
    item1 = todos_conteudos[current_index]
    item2 = todos_conteudos[(current_index + 1) % len(todos_conteudos)]
    
    return [item1, item2]

# --- CLASSES / MODELOS ---
class Flashcard:
    def __init__(self, frente: str, verso: str, idioma: str = 'Inglês'):
        self.frente = frente  
        self.verso = verso    
        self.idioma = idioma  

    def to_dict(self) -> dict:
        return {'frente': self.frente, 'verso': self.verso, 'idioma': self.idioma}

class Baralho:
    ARQUIVO_DADOS = FLASHCARDS_FILE
    
    def __init__(self):
        self.cartoes = []
        self._carregar_dados() 

    def adicionar_cartao(self, flashcard: Flashcard):
        self.cartoes.append(flashcard)
        self._salvar_dados()

    def _carregar_dados(self):
        try:
            with open(self.ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                self.cartoes = [Flashcard(**dado) for dado in dados]
        except (FileNotFoundError, json.JSONDecodeError):
            self.cartoes = [] 

    def _salvar_dados(self):
        dados_para_salvar = [cartao.to_dict() for cartao in self.cartoes]
        with open(self.ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
            json.dump(dados_para_salvar, f, ensure_ascii=False, indent=4)
            
    def buscar_todos(self):
        return self.cartoes

class User(UserMixin):
    def __init__(self, id, email, name, password_hash):
        self.id = str(id)
        self.email = email
        self.name = name
        self.password_hash = password_hash 

    @staticmethod
    def get_next_id():
        if not USERS: return 1
        return max([int(uid) for uid in USERS.keys()]) + 1

    @staticmethod
    def get(user_id):
        user_data = USERS.get(str(user_id))
        return User(**user_data) if user_data else None

    @staticmethod
    def get_by_email(email):
        for user_data in USERS.values():
            if user_data['email'].lower() == email.lower():
                return User(**user_data) 
        return None

    @staticmethod
    def create(name, email, password):
        global USERS
        if User.get_by_email(email): return None
        new_id = User.get_next_id()
        hashed_password = generate_password_hash(password)
        new_user_data = {'id': str(new_id), 'name': name, 'email': email, 'password_hash': hashed_password}
        USERS[str(new_id)] = new_user_data
        save_users(USERS)
        return User(**new_user_data)

# --- SETUP INICIAL ---
USERS = load_users()
if not USERS: User.create('Admin', 'admin@app.com', 'admin')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_bmvc4'
CHAT_HISTORY = []
socketio = SocketIO(app, cors_allowed_origins="*")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
 
baralho_principal = Baralho()

# --- ROTAS GERAIS ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/flashcards', methods=['GET', 'POST'])
@login_required
def pagina_flashcards():
    if request.method == 'POST':
        frente = request.form.get('frente')
        verso = request.form.get('verso')
        idioma = request.form.get('idioma', 'Desconhecido')
        if frente and verso:
            baralho_principal.adicionar_cartao(Flashcard(frente, verso, idioma))  
            flash('Flashcard adicionado!', 'success')
            return redirect(url_for('pagina_flashcards'))  
    return render_template('flashcards.html', cartoes=baralho_principal.buscar_todos())

@app.route('/revisar')
@login_required
def revisar():
    cartoes = baralho_principal.buscar_todos()
    if not cartoes: return jsonify({'erro': 'Nenhum flashcard.'}), 404
    return jsonify(random.choice(cartoes).to_dict())

# --- QUIZ ---
@app.route('/quiz')
@login_required
def pagina_quiz():
    return render_template('quiz.html')

@app.route('/api/iniciar_quiz')
@login_required
def api_iniciar_quiz():
    todos = baralho_principal.buscar_todos()
    if len(todos) < 4: return jsonify({'erro': True, 'mensagem': 'Precisa de 4 cartas.'})
    
    qtd = min(len(todos), 10)
    cartas = random.sample(todos, qtd)
    quiz_data = []
    
    for correta in cartas:
        opcoes = [c for c in todos if c.frente != correta.frente]
        erradas = random.sample(opcoes, min(len(opcoes), 3))
        alt = erradas + [correta]
        random.shuffle(alt)
        quiz_data.append({'pergunta': correta.frente, 'resposta_correta': correta.verso, 'alternativas': [c.verso for c in alt]})
    return jsonify(quiz_data)

# --- IMERSÃO (ATUALIZADO) ---
@app.route('/imersao')
@login_required
def pagina_imersao():
    todos = carregar_conteudos()
    if not todos:
        flash('Sem conteúdo disponível.', 'warning')
        return redirect(url_for('home'))
        
    conteudos_semana = obter_conteudo_semanal(todos)
    return render_template('imersao.html', conteudos=conteudos_semana)

@app.route('/api/salvar_rapido', methods=['POST'])
@login_required
def api_salvar_rapido():
    data = request.get_json()
    if data.get('frente') and data.get('verso'):
        baralho_principal.adicionar_cartao(Flashcard(data['frente'], data['verso'], "Inglês"))
        return jsonify({'sucesso': True})
    return jsonify({'erro': 'Dados inválidos'}), 400

# --- COMUNIDADE ---
@app.route('/comunidade')
@login_required
def pagina_comunidade():
    return render_template('comunidade.html', user=current_user, history=CHAT_HISTORY)

@socketio.on('enviar_mensagem')
def handle_mensagem(data):
    msg = data.get('mensagem')
    if msg and current_user.is_authenticated:
        timestamp = datetime.now().strftime('%H:%M')
        nova_msg = {'usuario': current_user.name, 'texto': msg, 'hora': timestamp}
        CHAT_HISTORY.append(nova_msg)
        if len(CHAT_HISTORY) > 50: CHAT_HISTORY.pop(0)
        emit('nova_mensagem', nova_msg, broadcast=True)

# --- ADMIN ---
@app.route('/dashboard_restrito')
@login_required
def dashboard_restrito():
    if current_user.email != 'admin@app.com':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('home'))
    return render_template('dashboard_restrito.html', user=current_user, all_users=USERS)

# --- AUTH ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        if User.create(request.form.get('name'), request.form.get('email'), request.form.get('password')):
            flash('Cadastro ok!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email em uso.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        user = User.get_by_email(request.form.get('email'))
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            flash(f'Bem-vindo, {user.name}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login falhou.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Saiu.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)