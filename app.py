from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user # importando login
import json
import random
import os

# --- Usuários Mokados - temporarios substituir por DB com senhas hasheadas ---
USERS = {
    'teste@email.com': {'email': 'teste@email.com', 'password': '123', 'id': 1, 'name': 'Usuário Teste'},
    'admin@email.com': {'email': 'admin@email.com', 'password': 'admin', 'id': 2, 'name': 'Administrador'}
}

# --- Define o caminho absoluto para o projeto (não alteradas) ---
basedir = os.path.abspath(os.path.dirname(__file__))

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

# ----------------- CLASSE USER PARA FLASK-LOGIN ----------------
class User(UserMixin):
    """Classe que representa um usuário para o Flask-Login."""
    def __init__(self, id, email, name):
        # o id precisa ser uma string para o Flask-Login
        self.id = str(id) 
        self.email = email
        self.name = name

    # Método estático para buscar usuário pelo ID
    @staticmethod
    def get(user_id):
        for user_data in USERS.values():
            if str(user_data['id']) == str(user_id):
                return User(user_data['id'], user_data['email'], user_data['name'])
        return None

# ----------------- INICIALIZAÇÃO E CONFIGURAÇÃO FLASK -----------------

app = Flask(__name__)
# Chave Secreta: para sessões seguras.
app.config['SECRET_KEY'] = 'uma_chave_secreta_aleatoria' 
baralho_principal = Baralho() 

# Configura o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
# Define para onde redirecionar se o usuário não estiver logado
login_manager.login_view = 'login' 
# Mensagem exibida para o usuário (opcional)
login_manager.login_message = "Por favor, faça login para acessar esta página." 
login_manager.login_message_category = "info"


# Loader de usuário: diz ao Flask-Login como carregar um usuário a partir do ID na sessão
@login_manager.user_loader
def load_user(user_id):
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para o login do usuário."""
    if current_user.is_authenticated:
        # Se já estiver logado, redireciona para a home
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') # Campo "Lembrar-me"

        # 1. Busca o usuário no dicionário (simulação de DB)
        user_data = USERS.get(email)

        # 2. Verifica se o usuário existe e se a senha está correta
        if user_data and user_data['password'] == password: 
            
            # Cria o objeto User para o Flask-Login
            user_obj = User(user_data['id'], user_data['email'], user_data['name'])
            
            # Faz o login do usuário na sessão
            # remember=True mantém o usuário logado após fechar o navegador
            login_user(user_obj, remember=bool(remember)) 
            
            # Redireciona o usuário para a página de origem (se houver) ou para a home
            next_page = request.args.get('next')
            flash(f'Bem-vindo(a), {user_data["name"]}!', 'success')
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
