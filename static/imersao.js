const modal = document.getElementById('modal-add');
const inputFrente = document.getElementById('modal-frente');
const inputVerso = document.getElementById('modal-verso');

// Detecta seleção de texto
document.addEventListener('mouseup', () => {
    const selecao = window.getSelection().toString().trim();
    
    // Se selecionou algo e o modal não está aberto
    if (selecao.length > 0 && modal.classList.contains('hidden')) {
        abrirModal(selecao);
    }
});

function abrirModal(textoSelecionado) {
    inputFrente.value = textoSelecionado;
    inputVerso.value = ''; // Limpa para o usuário digitar a tradução
    modal.classList.remove('hidden');
    inputVerso.focus();
}

function fecharModal() {
    modal.classList.add('hidden');
}

function salvarCardRapido() {
    const frente = inputFrente.value;
    const verso = inputVerso.value;

    if (!frente || !verso) {
        alert("Preencha a tradução!");
        return;
    }

    const btnSalvar = document.getElementById('btn-salvar-modal');
    const textoOriginal = btnSalvar.textContent;
    btnSalvar.textContent = "Salvando...";

    fetch('/api/salvar_rapido', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frente: frente, verso: verso })
    })
    .then(res => res.json())
    .then(data => {
        if (data.sucesso) {
            alert("Card salvo com sucesso!");
            fecharModal();
        } else {
            alert("Erro ao salvar.");
        }
    })
    .catch(err => console.error(err))
    .finally(() => {
        btnSalvar.textContent = textoOriginal;
    });
}