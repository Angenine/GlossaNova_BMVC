from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import random
import os 

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
            print(f"AVISO: Arquivo não encontrado em {self.ARQUIVO_DADOS}")
            self.cartoes = []
        except json.JSONDecodeError:
            print(f"AVISO: Erro ao decodificar o JSON em {self.ARQUIVO_DADOS}")
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

app = Flask(__name__)
baralho_principal = Baralho() 

@app.route('/')
def home():
    """Rota principal: Agora exibe o painel (dashboard)."""
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

    return render_template('flashcards.html', cartoes=baralho_principal.buscar_todos())

@app.route('/revisar')
def revisar():
    """Rota para revisão (API), retorna um flashcard aleatório em JSON."""
    cartoes = baralho_principal.buscar_todos()
    if not cartoes:
        return jsonify({'erro': 'Nenhum flashcard cadastrado.'}), 404
    
    cartao = random.choice(cartoes)
    return jsonify(cartao.to_dict())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
