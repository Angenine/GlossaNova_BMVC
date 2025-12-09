from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user # importando login
from werkzeug.security import generate_password_hash, check_password_hash # NOVO: Para hashing de senha
import json
import random
import os

# --- ARQUIVOS DE DADOS E CONSTANTES ---
basedir = os.path.abspath(os.path.dirname(__file__))
# NOVO: Caminho para o arquivo de usuários
USERS_FILE = os.path.join(basedir, 'users.json') 
FLASHCARDS_FILE = os.path.join(basedir, 'flashcards.json')

# --- HELPERS DE PERSISTÊNCIA DE USUÁRIOS (NOVOS) ---

def load_users():
    """Carrega a lista de usuários do arquivo JSON."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            # Chaves são os user_ids
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Cria um arquivo novo se estiver vazio/corrompido
        return {}

def save_users(users_data):
    """Salva a lista atual de usuários no arquivo JSON."""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        # Garante que as chaves sejam strings (IDs)
        data_to_save = {str(k): v for k, v in users_data.items()}
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# ----------------- CLASSES DE DADOS E LÓGICA -----------------

class Flashcard:
    def __init__(self, frente: str, verso: str, idioma: str = 'Inglês'):
        self.frente = frente  
        self.verso = verso    
        self.idioma = idioma  

    def to_dict(self) -> dict[str, str]:
        return {
            'frente': self.frente,
            'verso': self.verso,
            'idioma': self.idioma
        }

    def __str__(self):
        """Representação legível do objeto."""
        return f"Flashcard ({self.idioma}): {self.frente} -> {self.verso}"

class Baralho:
    
    # Usa o caminho absoluto para encontrar o JSON
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
        except FileNotFoundError:
            # Se não achar, cria lista vazia
            self.cartoes = []
        except json.JSONDecodeError:
            # Se o arquivo estiver corrompido/vazio
            self.cartoes = [] 

    def _salvar_dados(self):
        """Salva os flashcards no arquivo JSON."""
        dados_para_salvar = [cartao.to_dict() for cartao in self.cartoes]
        with open(self.ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
            json.dump(dados_para_salvar, f, ensure_ascii=False, indent=4)
            
    def buscar_todos(self):
        """Retorna a lista de todos os flashcards."""
        return self.cartoes

    def buscar_por_indice(self, indice: int) -> 'Flashcard | None':
        """Retorna um flashcard pelo índice, se existir."""
        if 0 <= indice < len(self.cartoes):
            return self.cartoes[indice]
        return None

# ----------------- CLASSE USER PARA FLASK-LOGIN (ATUALIZADA) ----------------
class User(UserMixin):
    """Classe que representa um usuário para o Flask-Login."""
    # NOVO: Inclui password_hash para autenticação segura
    def __init__(self, id, email, name, password_hash):
        self.id = str(id)
        self.email = email
        self.name = name
        self.password_hash = password_hash 

    @staticmethod
    def get_next_id():
        """Gera o próximo ID sequencial baseado nas chaves existentes."""
        if not USERS:
            return 1
        return max([int(uid) for uid in USERS.keys()]) + 1

    @staticmethod
    def get(user_id):
        """Busca um usuário pelo ID na base de dados carregada."""
        user_data = USERS.get(str(user_id))
        if not user_data:
            return None
        # Desempacota o dicionário para criar o objeto User
        return User(**user_data) 

    @staticmethod
    def get_by_email(email):
        """Busca um usuário pelo e-mail (usado no login)."""
        for user_data in USERS.values():
            if user_data['email'].lower() == email.lower():
                # Retorna o objeto User com os dados encontrados
                return User(**user_data) 
        return None

    @staticmethod
    def create(name, email, password):
        """Cria, hashea e persiste um novo usuário no JSON."""
        global USERS
        
        # 1. Verifica se o usuário já existe
        if User.get_by_email(email):
            return None
        
        # 2. Gera ID e hash
        new_id = User.get_next_id()
        # CRIPTOGRAFIA DE SENHA
        hashed_password = generate_password_hash(password)
        
        # 3. Prepara os dados
        new_user_data = {
            'id': str(new_id),
            'name': name,
            'email': email,
            'password_hash': hashed_password # Salva o hash
        }
        
        # 4. Adiciona ao dicionário em memória
        USERS[str(new_id)] = new_user_data
        
        # 5. Persiste no JSON
        save_users(USERS)
        
        return User(**new_user_data)

# ----------------- INICIALIZAÇÃO E CONFIGURAÇÃO FLASK -----------------

# NOVO: Carrega usuários persistentes (ou vazio se o arquivo não existir)
USERS = load_users()

# Inicialização de Usuários Mockados (Apenas na primeira execução se USERS estiver vazio)
if not USERS:
    print("--- Criando usuários iniciais e persistindo em users.json ---")
    User.create(name='Usuário Teste', email='teste@email.com', password='123')
    User.create(name='Administrador', email='admin@email.com', password='admin')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_aleatoria'
baralho_principal = Baralho()

# Configura o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"


# Loader de usuário
@login_manager.user_loader
def load_user(user_id):
    # Usa o método estático atualizado
    return User.get(user_id)
 
# --- ROTAS (COM NOVOS AJUSTES) ---

@app.route('/')
def home():
    """Rota principal: Dashboard."""
    # current_user está disponível graças ao Flask-Login.
    # Verifica se o usuário está autenticado e passa para o template
    return render_template('index.html')

@app.route('/flashcards', methods=['GET', 'POST'])
@login_required # Apenas usuários logados podem acessar esta página
def pagina_flashcards():
    """Rota para a página de flashcards (adicionar e listar)."""
    
    if request.method == 'POST':
        frente = request.form.get('frente')
        verso = request.form.get('verso')
        idioma = request.form.get('idioma', 'Desconhecido')
        
        if frente and verso:
            novo_cartao = Flashcard(frente, verso, idioma)  
            baralho_principal.adicionar_cartao(novo_cartao)  
            # Usando flash para exibir mensagem de sucesso
            flash('Flashcard adicionado com sucesso!', 'success')
            return redirect(url_for('pagina_flashcards'))  

    return render_template('flashcards.html', cartoes=baralho_principal.buscar_todos())

@app.route('/revisar')
def revisar():
    """Rota para revisão (API), retorna um flashcard aleatório em JSON."""
    cartoes = baralho_principal.buscar_todos()
    if not cartoes:
        return jsonify({'erro': 'Nenhum flashcard cadastrado.'}), 404
    
    cartao = random.choice(cartoes)
    return jsonify(cartao.to_dict())

# --- ROTAS DO QUIZ (NOVO) ---

@app.route('/quiz')
def pagina_quiz():
    """Renderiza a página HTML do desafio."""
    return render_template('quiz.html')

@app.route('/api/iniciar_quiz')
def api_iniciar_quiz():
    """Gera uma partida completa com até 10 perguntas."""
    todos_cartoes = baralho_principal.buscar_todos()
    
    # Validação: Precisamos de pelo menos 4 cartões
    if len(todos_cartoes) < 4:
        return jsonify({
            'erro': True, 
            'mensagem': 'Você precisa de pelo menos 4 flashcards para jogar!'
        })

    # Define quantas perguntas terá o quiz (máximo 10 ou o total de cartas)
    qtd_perguntas = min(len(todos_cartoes), 10)
    
    # Seleciona as cartas que serão as perguntas da rodada
    cartas_pergunta = random.sample(todos_cartoes, qtd_perguntas)
    
    quiz_data = []

    for correta in cartas_pergunta:
        # Para cada pergunta, escolhemos 3 erradas
        opcoes_disponiveis = [c for c in todos_cartoes if c.frente != correta.frente]
        
        # Garante que temos erradas suficientes
        qtd_erradas = min(len(opcoes_disponiveis), 3)
        erradas = random.sample(opcoes_disponiveis, qtd_erradas)
        
        alternativas = erradas + [correta]
        random.shuffle(alternativas)

        quiz_data.append({
            'pergunta': correta.frente,
            'resposta_correta': correta.verso,
            'alternativas': [c.verso for c in alternativas]
        })
    
    return jsonify(quiz_data)

# ... (Mantenha os imports e classes anteriores)

# --- NOVA CLASSE ---
class ConteudoImersao:
    def __init__(self, titulo, tipo, texto_original, traducao):
        self.titulo = titulo
        self.tipo = tipo # Ex: Música, Texto, Notícia
        self.texto_original = texto_original
        self.traducao = traducao

# --- DADOS MOCKADOS (Simulando o banco de conteúdos) ---
# Você pode adicionar mais textos aqui depois
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


@app.route('/imersao')
def pagina_imersao():
    """Mostra o texto da semana (pega o primeiro da lista por enquanto)."""
    conteudo = conteudos_imersao[0] # Pega o primeiro texto
    return render_template('imersao.html', conteudo=conteudo)

@app.route('/api/salvar_rapido', methods=['POST'])
def api_salvar_rapido():
    """API para salvar flashcard via AJAX (sem recarregar a página)."""
    data = request.get_json()
    frente = data.get('frente')
    verso = data.get('verso')
    
    if frente and verso:
        novo_cartao = Flashcard(frente, verso, "Inglês")
        baralho_principal.adicionar_cartao(novo_cartao)
        return jsonify({'sucesso': True})
    
    return jsonify({'erro': 'Dados inválidos'}), 400

# Rota protegida que só o admin pode ver
@app.route('/dashboard_restrito')
@login_required # Apenas usuários logados podem acessar
def dashboard_restrito():
    """Rota restrita a usuários logados."""
    # Exemplo de verificação de permissão (não é o ideal, mas funciona para um mock)
    if current_user.email != 'admin@app.com':
        flash('Você não tem permissão para acessar esta área.', 'danger')
        return redirect(url_for('home'))
        
    return render_template('dashboard_restrito.html', user=current_user)
    
# ----------------- NOVAS ROTAS DE AUTENTICAÇÃO -----------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registrar novos usuários e persistir no JSON."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('register.html')

        new_user = User.create(name, email, password)

        if new_user:
            flash('Cadastro realizado com sucesso! Faça seu login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('O e-mail já está em uso.', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para o login do usuário (Atualizada para usar hash e persistência)."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        # 1. Busca o usuário pelo email usando a base persistente
        user = User.get_by_email(email)

        # 2. Verifica se o usuário existe E se a senha criptografada confere
        if user and check_password_hash(user.password_hash, password):
            
            # Faz o login do usuário
            login_user(user, remember=remember)
            
            # Redireciona para a próxima página ou para a home
            next_page = request.args.get('next')
            flash(f'Bem-vindo(a) de volta, {user.name}!', 'success')
            return redirect(next_page or url_for('home'))
        else:
            # Mensagem de erro
            flash('E-mail ou senha inválidos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Rota para o logout do usuário."""
    logout_user()
    flash('Você saiu da sua conta com sucesso.', 'info')
    return redirect(url_for('home'))
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
