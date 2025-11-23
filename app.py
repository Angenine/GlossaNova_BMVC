from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import random
import os

# --- Define o caminho absoluto para o projeto ---
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

# --- Código Flask ---
app = Flask(__name__)
baralho_principal = Baralho() 

# --- ROTAS ---

@app.route('/')
def home():
    """Rota principal: Dashboard."""
    return render_template('index.html')

@app.route('/flashcards', methods=['GET', 'POST'])
def pagina_flashcards():
    """Rota para a página de flashcards (adicionar e listar)."""
    
    if request.method == 'POST':
        frente = request.form.get('frente')
        verso = request.form.get('verso')
        idioma = request.form.get('idioma', 'Desconhecido')
        
        if frente and verso:
            novo_cartao = Flashcard(frente, verso, idioma) 
            baralho_principal.adicionar_cartao(novo_cartao) 
            return redirect(url_for('pagina_flashcards')) 

    # Exibição (GET)
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)