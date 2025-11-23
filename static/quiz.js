// static/quiz.js

let perguntas = [];      // Lista de perguntas da partida atual
let indiceAtual = 0;     // Qual pergunta estamos respondendo
let acertos = 0;
let erros = 0;
let respondido = false;  // Bloqueia cliques múltiplos

// Referências DOM
const quizContainer = document.getElementById('quiz-container');
const endScreen = document.getElementById('end-screen'); // Novo container
const loadingContainer = document.getElementById('loading'); // Se tiver
const errorContainer = document.getElementById('error-message');
const questionText = document.getElementById('question-text');
const optionsGrid = document.getElementById('options-grid');
const scoreDisplay = document.getElementById('score-display');

// Referências do Fim de Jogo
const finalAcertos = document.getElementById('final-acertos');
const finalErros = document.getElementById('final-erros');

function iniciarQuiz() {
    // Reseta variaveis
    perguntas = [];
    indiceAtual = 0;
    acertos = 0;
    erros = 0;
    scoreDisplay.textContent = "Pontuação: 0";
    
    // Controla visibilidade das telas
    quizContainer.classList.remove('hidden');
    endScreen.classList.add('hidden');
    errorContainer.classList.add('hidden');
    
    // Estado de carregamento
    optionsGrid.style.opacity = '0.5';
    questionText.textContent = 'Gerando partida...';
    optionsGrid.innerHTML = '';

    fetch('/api/iniciar_quiz')
        .then(response => response.json())
        .then(data => {
            optionsGrid.style.opacity = '1';

            if (data.erro) {
                quizContainer.classList.add('hidden');
                errorContainer.classList.remove('hidden');
                document.getElementById('msg-erro-texto').textContent = data.mensagem;
                return;
            }

            // Salva a lista de perguntas e mostra a primeira
            perguntas = data;
            mostrarPerguntaAtual();
        })
        .catch(err => {
            console.error(err);
            questionText.textContent = "Erro ao conectar com o servidor.";
        });
}

function mostrarPerguntaAtual() {
    // Verifica se acabou as perguntas
    if (indiceAtual >= perguntas.length) {
        finalizarJogo();
        return;
    }

    respondido = false;
    const dados = perguntas[indiceAtual];
    
    // Atualiza texto
    questionText.textContent = dados.pergunta;
    
    // Limpa e cria botões
    optionsGrid.innerHTML = '';
    
    dados.alternativas.forEach(opcao => {
        const btn = document.createElement('button');
        btn.className = "w-full p-4 text-lg font-medium text-gray-700 bg-white border-2 border-gray-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-all duration-200";
        btn.textContent = opcao;
        
        btn.onclick = () => verificarResposta(btn, opcao, dados.resposta_correta);
        
        optionsGrid.appendChild(btn);
    });
}

function verificarResposta(botaoClicado, respostaEscolhida, respostaCorreta) {
    if (respondido) return; 
    respondido = true;

    const botoes = optionsGrid.querySelectorAll('button');

    if (respostaEscolhida === respostaCorreta) {
        // Acertou
        botaoClicado.classList.remove('bg-white', 'border-gray-200');
        botaoClicado.classList.add('bg-green-100', 'border-green-500', 'text-green-700');
        acertos++;
    } else {
        // Errou
        botaoClicado.classList.remove('bg-white', 'border-gray-200');
        botaoClicado.classList.add('bg-red-100', 'border-red-500', 'text-red-700');
        erros++;
        
        // Mostra a correta
        botoes.forEach(btn => {
            if (btn.textContent === respostaCorreta) {
                btn.classList.remove('bg-white', 'border-gray-200');
                btn.classList.add('bg-green-100', 'border-green-500', 'text-green-700');
            }
        });
    }

    // Atualiza pontuação na tela
    scoreDisplay.textContent = `Pontuação: ${acertos}`;

    // Espera 1.5s e vai para a próxima
    setTimeout(() => {
        indiceAtual++;
        mostrarPerguntaAtual();
    }, 1500);
}

function finalizarJogo() {
    // Esconde o quiz e mostra a tela final
    quizContainer.classList.add('hidden');
    endScreen.classList.remove('hidden');

    // Preenche os dados
    finalAcertos.textContent = acertos;
    finalErros.textContent = erros;
}

// Inicia ao carregar a página
document.addEventListener('DOMContentLoaded', iniciarQuiz);