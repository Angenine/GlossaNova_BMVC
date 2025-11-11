from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import random

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
## Arquivo: app.py 
class Baralho:
    
    # Nome do arquivo de armazenamento
    ARQUIVO_DADOS = 'flashcards.json' 
    
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
                # Recria os objetos Flashcard a partir dos dados do JSON
                self.cartoes = [Flashcard(**dado) for dado in dados]
        except FileNotFoundError:
            # Cria um arquivo JSON vazio se não existir
            self.cartoes = []
        except json.JSONDecodeError:
            # Caso o arquivo esteja corrompido ou vazio
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
baralho_principal = Baralho() # Instancia o Baralho (Objeto POO)

@app.route('/', methods=['GET', 'POST'])
def home():
    """Rota principal: Cria novos flashcards e exibe a lista."""
    
    if request.method == 'POST':
        # 1. Criação de Novo Flashcard (Lógica POO)
        frente = request.form.get('frente')
        verso = request.form.get('verso')
        idioma = request.form.get('idioma', 'Desconhecido')
        
        if frente and verso:
            novo_cartao = Flashcard(frente, verso, idioma) # Cria o Objeto
            baralho_principal.adicionar_cartao(novo_cartao) # Usa o método POO
            return redirect(url_for('home')) # Redireciona para evitar reenvio de formulário

    # 2. Exibição
    # A página index.html será renderizada (ver próxima seção)
    return render_template('index.html', cartoes=baralho_principal.buscar_todos())


@app.route('/revisar')
def revisar():
    """Rota para revisão, retorna um flashcard aleatório em formato JSON."""
    cartoes = baralho_principal.buscar_todos()
    if not cartoes:
        return jsonify({'erro': 'Nenhum flashcard cadastrado.'}), 404
    
    # Seleciona um cartão aleatório
    cartao = random.choice(cartoes)
    
    # Retorna o cartão em formato JSON para o JavaScript lidar com a exibição
    return jsonify(cartao.to_dict())

if __name__ == '__main__':
    # Para rodar, digite 'python app.py' no terminal
    app.run(host='0.0.0.0', port=8000, debug=True)