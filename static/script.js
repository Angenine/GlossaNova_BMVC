let cartaoAtual = null;
let isFlipped = false; 

const flashcardBox = document.getElementById('flashcard-box');
const cardFrente = document.getElementById('card-frente');
const cardVerso = document.getElementById('card-verso');
const idiomaDisplay = document.getElementById('idioma-display');


function carregarNovoCartao() {
    // 1. Reseta o estado visual do cartão (volta para a frente)
    if (isFlipped) {
        flashcardBox.classList.remove('flipped');
        isFlipped = false;
    }
    
    // 2. Mostra um estado de carregamento
    cardFrente.textContent = 'Carregando...';
    cardVerso.textContent = ''; // Limpa o verso
    idiomaDisplay.textContent = '';

    // 3. Busca o novo card
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
            cardFrente.textContent = cartaoAtual.frente;
            cardVerso.textContent = cartaoAtual.verso;
            idiomaDisplay.textContent = `Idioma: ${cartaoAtual.idioma}`;
        })
        .catch(error => {
            console.error('Erro ao buscar o flashcard:', error);
            cardFrente.textContent = 'Erro ao carregar (ver console).';
            cardVerso.textContent = '';
            idiomaDisplay.textContent = '';
        });
}

function virarCartao() {
    if (!cartaoAtual) {
        cardFrente.textContent = 'Clique em "Revisar Próxima Palavra" para começar!';
        return;
    }
    isFlipped = !isFlipped;
    flashcardBox.classList.toggle('flipped');
}

document.addEventListener('DOMContentLoaded', carregarNovoCartao);