from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_socketio import SocketIO, emit
import json
import random
import os
from datetime import datetime

# --- ARQUIVOS DE DADOS E CONSTANTES ---
basedir = os.path.abspath(os.path.dirname(__file__))
USERS_FILE = os.path.join(basedir, 'users.json') 
FLASHCARDS_FILE = os.path.join(basedir, 'flashcards.json')

# --- PERSISTÊNCIA DE USUÁRIOS ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_users(users_data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        data_to_save = {str(k): v for k, v in users_data.items()}
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# ----------------- CLASSES DE DADOS E LÓGICA -----------------

class Flashcard:
    def __init__(self, frente: str, verso: str, idioma: str = 'Inglês'):
        self.frente = frente  
        self.verso = verso    
        self.idioma = idioma  

    def to_dict(self) -> dict[str, str]:
        return {'frente': self.frente, 'verso': self.verso, 'idioma': self.idioma}

class Baralho:
    ARQUIVO_DADOS = os.path.join(basedir, 'flashcards.json') 
    
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

# --- CLASSE DE CONTEÚDO (IMERSÃO) ---
class ConteudoImersao:
    def __init__(self, titulo, tipo, texto_original, traducao):
        self.titulo = titulo
        self.tipo = tipo 
        self.texto_original = texto_original
        self.traducao = traducao

# Conteúdos Mockados
conteudos_imersao = [
    ConteudoImersao(
        titulo="Yellow Submarine - The Beatles",
        tipo="Música",
        texto_original="In the town where I was born\nLived a man who sailed to sea\nAnd he told us of his life\nIn the land of submarines",
        traducao="Na cidade onde eu nasci\nViveu um homem que navegou para o mar\nE ele nos contou sobre sua vida\nNa terra dos submarinos"
    ),
    ConteudoImersao(
        titulo="O Pequeno Príncipe (Trecho)",
        tipo="Livro",
        texto_original="And now here is my secret, a very simple secret: It is only with the heart that one can see rightly; what is essential is invisible to the eye.",
        traducao="E aqui está o meu segredo, um segredo muito simples: Só se vê bem com o coração; o essencial é invisível aos olhos."
    )
]

# --- CLASSE USER (AUTH) ---
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

# ----------------- INICIALIZAÇÃO -----------------

USERS = load_users()
# Cria admin se não existir
if not USERS:
    User.create(name='Admin', email='admin@app.com', password='admin')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_bmvc4'

# CONFIGURAÇÃO DO SOCKETIO
socketio = SocketIO(app, cors_allowed_origins="*")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
 
baralho_principal = Baralho()

# --- ROTAS PRINCIPAIS ---

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
            novo_cartao = Flashcard(frente, verso, idioma)  
            baralho_principal.adicionar_cartao(novo_cartao)  
            flash('Flashcard adicionado!', 'success')
            return redirect(url_for('pagina_flashcards'))  
    return render_template('flashcards.html', cartoes=baralho_principal.buscar_todos())

@app.route('/revisar')
def revisar():
    cartoes = baralho_principal.buscar_todos()
    if not cartoes: return jsonify({'erro': 'Nenhum flashcard.'}), 404
    cartao = random.choice(cartoes)
    return jsonify(cartao.to_dict())

# --- ROTAS QUIZ ---

@app.route('/quiz')
def pagina_quiz():
    return render_template('quiz.html')

@app.route('/api/iniciar_quiz')
def api_iniciar_quiz():
    todos_cartoes = baralho_principal.buscar_todos()
    if len(todos_cartoes) < 4: return jsonify({'erro': True, 'mensagem': 'Precisa de 4 cartas.'})
    qtd = min(len(todos_cartoes), 10)
    cartas = random.sample(todos_cartoes, qtd)
    quiz_data = []
    for correta in cartas:
        opcoes = [c for c in todos_cartoes if c.frente != correta.frente]
        erradas = random.sample(opcoes, min(len(opcoes), 3))
        alt = erradas + [correta]
        random.shuffle(alt)
        quiz_data.append({'pergunta': correta.frente, 'resposta_correta': correta.verso, 'alternativas': [c.verso for c in alt]})
    return jsonify(quiz_data)

# --- ROTAS IMERSÃO ---

@app.route('/imersao')
def pagina_imersao():
    """Mostra o texto da semana."""
    conteudo = conteudos_imersao[0] 
    return render_template('imersao.html', conteudo=conteudo)

@app.route('/api/salvar_rapido', methods=['POST'])
def api_salvar_rapido():
    """API para salvar flashcard via AJAX."""
    data = request.get_json()
    frente = data.get('frente')
    verso = data.get('verso')
    if frente and verso:
        novo_cartao = Flashcard(frente, verso, "Inglês")
        baralho_principal.adicionar_cartao(novo_cartao)
        return jsonify({'sucesso': True})
    return jsonify({'erro': 'Dados inválidos'}), 400

# --- ROTA DE ACESSO RESTRITO =---

@app.route('/dashboard_restrito')
@login_required  # Protege a rota: só logado entra
def dashboard_restrito():
    """Página exclusiva para administradores."""
    # Verificação de permissão (Simples)
    if current_user.email != 'admin@app.com':
        flash('Acesso negado: Esta área é restrita a administradores.', 'danger')
        return redirect(url_for('home'))
    
    # Se for admin, renderiza a página
    return render_template('dashboard_restrito.html', user=current_user)

CHAT_HISTORY = []

# --- ROTA DA COMUNIDADE (WEBSOCKET) ---

@app.route('/comunidade')
@login_required
def pagina_comunidade():
    """Renderiza a sala de chat e passa o histórico."""
    # Passamos o CHAT_HISTORY para o HTML
    return render_template('comunidade.html', user=current_user, history=CHAT_HISTORY)

# --- EVENTOS WEBSOCKET ---

@socketio.on('connect')
def handle_connect():
    print(f"Cliente conectado: {current_user.name if current_user.is_authenticated else 'Anon'}")

@socketio.on('enviar_mensagem')
def handle_mensagem(data):
    """Recebe mensagem, salva no histórico e retransmite."""
    msg = data.get('mensagem')
    if msg and current_user.is_authenticated:
        timestamp = datetime.now().strftime('%H:%M')
        
        # Cria o objeto da mensagem
        nova_msg = {
            'usuario': current_user.name,
            'texto': msg,
            'hora': timestamp
        }
        
        # 1. Salva na memória do servidor
        CHAT_HISTORY.append(nova_msg)
        
        # Opcional: Limita o histórico às últimas 50 mensagens para não pesar
        if len(CHAT_HISTORY) > 50:
            CHAT_HISTORY.pop(0)

        # 2. Emite para TODOS os conectados
        emit('nova_mensagem', nova_msg, broadcast=True)

# --- ROTAS AUTH ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.create(name, email, password):
            flash('Cadastro ok!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email em uso.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.get_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Olá, {user.name}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Erro no login.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Saiu.', 'info')
    return redirect(url_for('home'))

# --- EXECUÇÃO ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)