// Arquivo: static/script.js

let cartaoAtual = null; 
let isFlipped = false; // Indica se o cartão está virado para o verso

const flashcardBox = document.getElementById('flashcard-box');
const cardFrente = document.getElementById('card-frente');
const cardVerso = document.getElementById('card-verso');
const idiomaDisplay = document.getElementById('idioma-display');

/**
 * Função para carregar um novo flashcard aleatório do backend.
 */
function carregarNovoCartao() {
    // Reseta o estado visual do cartão antes de carregar um novo
    if (isFlipped) {
        flashcardBox.classList.remove('flipped');
        isFlipped = false;
    }
    
    // Mostra um estado de carregamento
    cardFrente.textContent = 'Carregando...';
    cardVerso.textContent = '';
    cardFrente.style.opacity = '1';
    cardVerso.style.opacity = '0';
    idiomaDisplay.textContent = '';

    fetch('/revisar') 
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao carregar o cartão. Status: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (data.erro) {
                cardFrente.textContent = data.erro;
                cardVerso.textContent = '';
                idiomaDisplay.textContent = '';
                cartaoAtual = null;
                return;
            }
            
            cartaoAtual = data;
            
            // Atualiza o conteúdo HTML
            cardFrente.textContent = cartaoAtual.frente;
            cardVerso.textContent = cartaoAtual.verso;
            idiomaDisplay.textContent = `Idioma: ${cartaoAtual.idioma}`;

            // Garante que a frente está visível e o verso oculto para o novo cartão
            cardFrente.style.opacity = '1';
            cardVerso.style.opacity = '0';

        })
        .catch(error => {
            console.error('Erro ao buscar o flashcard:', error);
            cardFrente.textContent = 'Erro ao carregar (ver console).';
            cardVerso.textContent = '';
            idiomaDisplay.textContent = '';
        });
}

/**
 * Função para alternar a exibição entre frente e verso do flashcard com animação.
 */
function virarCartao() {
    if (!cartaoAtual) {
        cardFrente.textContent = 'Clique em "Revisar Próxima Palavra" para começar!';
        return;
    }

    // Alterna a classe 'flipped' para iniciar a animação CSS
    flashcardBox.classList.toggle('flipped');
    isFlipped = !isFlipped;

    // Ajusta a opacidade para transição suave do texto (após a rotação)
    setTimeout(() => {
        if (isFlipped) {
            cardFrente.style.opacity = '0';
            cardVerso.style.opacity = '1';
        } else {
            cardFrente.style.opacity = '1';
            cardVerso.style.opacity = '0';
        }
    }, 300); // Metade do tempo da animação de rotação (0.6s total)
}

// Carrega o primeiro cartão assim que a página é carregada
document.addEventListener('DOMContentLoaded', carregarNovoCartao);