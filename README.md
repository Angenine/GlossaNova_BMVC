#  GlossaNova: Plataforma de Aprendizado de Idiomas 

##  Visão Geral do Projeto

O GlossaNova é um Produto Mínimo Viável (MVP) desenvolvido com **Flask** e **WebSockets**, focado em transformar o aprendizado de idiomas em uma experiência social, interativa e persistente. O projeto estabelece uma arquitetura robusta para gerenciar vocabulário, oferecer prática contextualizada e, crucialmente, suportar comunicação em tempo real entre usuários.

##  Funcionalidades Principais

O GlossaNova está estruturado em quatro pilares de aprendizado, acessíveis diretamente do Dashboard:

### 1. Sala de Estudos Global (Comunicação em Tempo Real)
* **Tempo Real com WebSockets:** Implementação de comunicação bidirecional *Full-Duplex* utilizando **Flask-SocketIO**. O servidor transmite mensagens instantaneamente a todos os usuários logados.
* **Atualização Assíncrona:** As mensagens de chat são enviadas e recebidas sem a necessidade de recarregar a página, garantindo fluidez e uma verdadeira experiência de tempo real.

### 2.  Flashcards Personalizados (Vocabulário)
* **Criação e Persistência:** Os usuários podem cadastrar novas palavras (frente) e traduções (verso). Os dados são persistidos no arquivo `flashcards.json`.
* **Revisão:** Sistema para a prática e gerenciamento do vocabulário customizado do estudante.

### 3. Imersão Semanal (Leitura Contextual)
* **Conteúdo Autêntico:** Exibição de trechos de leitura para prática contextual.
* **Quick Save (Salvar Rápido):** Recurso que permite ao usuário selecionar uma palavra desconhecida no texto e salvá-la instantaneamente como um novo Flashcard (via API/AJAX).

### 4. Quiz Interativo (Avaliação)
* **Geração Dinâmica:** Quizzes de múltipla escolha onde as perguntas e as opções de resposta são geradas de forma dinâmica a partir do vocabulário já cadastrado pelo próprio estudante, personalizando a avaliação.

## Tecnologias e Arquitetura

O projeto utiliza Python e o micro-framework Flask para o backend, com foco em autenticação segura e comunicação assíncrona.

| Componente | Tecnologia | Uso |
| :--- | :--- | :--- |
| **Back-end** | **Flask** | Roteamento principal e lógica da aplicação. |
| **Tempo Real** | **Flask-SocketIO** | Habilita os WebSockets para a Sala de Estudos Global. |
| **Autenticação** | **Flask-Login** | Gerenciamento de sessões de usuário (`@login_required`). |
| **Segurança** | **Werkzeug Security** | Essencial para o *hashing* seguro de senhas no cadastro. |
| **Persistência** | **JSON** | Utilizado como 'banco de dados' para persistir `users.json` e `flashcards.json`. |
| **Front-end** | Jinja2, Tailwind CSS | Templates dinâmicos e estilização responsiva. |

##  Segurança e Persistência de Dados

* **Cadastro Seguro:** Na rota `/register`, as senhas são criptografadas (hasheadas) usando `werkzeug.security` antes de serem salvas no `users.json`.
* **Sessão:** O Flask-Login gerencia a sessão, redirecionando usuários não autenticados para `/login`.
* **Dados:** Todos os Flashcards criados são salvos e carregados do `flashcards.json`, garantindo que o progresso do usuário seja mantido entre as sessões.

## Como Rodar o Projeto

Para configurar e executar o GlossaNova localmente, siga os passos abaixo:

### 1. Clone o repositório

```bash
git clone [URL_DO_SEU_REPOSITORIO]
cd GlossaNova
````

### 2\. Crie e ative o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3\. Instale as dependências

```bash
pip install Flask Flask-Login werkzeug Flask-SocketIO
```

### 4\. Execute o Servidor

É obrigatório utilizar o `socketio.run` para que a comunicação WebSocket funcione:

```bash
python app.py
```

### 5\. Acesso

O servidor estará disponível em `http://0.0.0.0:8000`.

**Credenciais Padrão (Se os arquivos JSON ainda não existirem):**

  * **E-mail:** `teste@email.com`
  * **Senha:** `123`

Você também pode se cadastrar através da rota `/register`.

```
```
