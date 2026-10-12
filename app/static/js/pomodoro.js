/* FísicaFlow — tela de Pomodoro
 *
 * O cronômetro roda no navegador, mas os PONTOS só saem do servidor:
 *   1. ao apertar "Iniciar" no Foco, o servidor abre uma sessão (guarda a hora);
 *   2. quando o tempo acaba, pedimos para o servidor concluir a sessão;
 *   3. o servidor confere se o tempo passou de verdade e só então dá os pontos.
 * Assim ninguém ganha pontos chamando a API direto.
 *
 * O tempo restante é calculado pelo RELÓGIO (hora de término), e não contando
 * "ticks": se o navegador deixar a aba em segundo plano mais lenta, o
 * cronômetro continua certo.
 */
(function () {
  'use strict';

  var page = document.querySelector('[data-pomodoro-page]');
  if (!page) return;

  var RAIO = 110;
  var CIRCUNFERENCIA = 2 * Math.PI * RAIO;
  var CHAVE = 'ff-pomodoro';

  var ring = page.querySelector('[data-ring]');
  var digits = page.querySelector('[data-digits]');
  var modeLabel = page.querySelector('[data-mode-label]');
  var botaoPlay = page.querySelector('[data-toggle]');
  var botaoReset = page.querySelector('[data-reset]');
  var abas = page.querySelectorAll('[data-mode-tab]');
  var settingsModal = page.querySelector('[data-modal="settings"]');
  var settingsForm = page.querySelector('[data-settings-form]');
  var tituloOriginal = document.title;

  /* ---- durações escolhidas (ficam salvas neste navegador) ---- */
  var limiteFoco = {
    min: Number(page.dataset.focusMin),
    max: Number(page.dataset.focusMax)
  };

  function limitar(valor, min, max, padrao) {
    var n = parseInt(valor, 10);
    if (isNaN(n)) return padrao;
    return Math.min(max, Math.max(min, n));
  }

  function carregarConfig() {
    var salvo = {};
    try { salvo = JSON.parse(localStorage.getItem(CHAVE)) || {}; } catch (e) { /* sem storage */ }
    return {
      focus: limitar(salvo.focus, limiteFoco.min, limiteFoco.max, 25),
      pause: limitar(salvo.pause, 1, 30, 5)
    };
  }

  var config = carregarConfig();

  /* ---- estado do cronômetro ---- */
  var estado = {
    mode: 'foco',        // 'foco' | 'descanso'
    running: false,
    remaining: config.focus * 60,   // segundos
    endsAt: 0,           // hora (em ms) em que o tempo acaba, enquanto roda
    sessionId: null,     // sessão de foco aberta no servidor
    busy: false          // esperando resposta do servidor
  };
  var relogio = null;

  function total() {
    return (estado.mode === 'foco' ? config.focus : config.pause) * 60;
  }

  function dois(n) { return (n < 10 ? '0' : '') + n; }

  /* ---- desenho ---- */
  function desenhar() {
    var restante = estado.remaining;
    var texto = dois(Math.floor(restante / 60)) + ':' + dois(restante % 60);
    var progresso = (total() - restante) / total();

    digits.textContent = texto;
    modeLabel.textContent = estado.mode === 'foco' ? 'Foco' : 'Descanso';
    ring.setAttribute('stroke-dasharray', CIRCUNFERENCIA);
    ring.setAttribute('stroke-dashoffset', CIRCUNFERENCIA * (1 - progresso));

    page.classList.toggle('is-break', estado.mode === 'descanso');
    page.classList.toggle('is-running', estado.running);
    botaoPlay.setAttribute('aria-label', estado.running ? 'Pausar' : 'Iniciar');

    abas.forEach(function (aba) {
      var ativa = aba.dataset.modeTab === estado.mode;
      aba.classList.toggle('is-active', ativa);
      aba.setAttribute('aria-pressed', String(ativa));
    });

    // mostra o tempo na aba do navegador enquanto roda
    document.title = estado.running ? texto + ' · ' + tituloOriginal : tituloOriginal;
  }

  /* ---- controle ---- */
  function pararRelogio() {
    if (relogio) { clearInterval(relogio); relogio = null; }
  }

  function segundosRestantes() {
    return Math.max(0, Math.ceil((estado.endsAt - Date.now()) / 1000));
  }

  function tique() {
    estado.remaining = segundosRestantes();
    desenhar();
    if (estado.remaining <= 0) terminar();
  }

  function rodar() {
    estado.endsAt = Date.now() + estado.remaining * 1000;
    estado.running = true;
    pararRelogio();
    relogio = setInterval(tique, 250);
    desenhar();
  }

  function pausar() {
    pararRelogio();
    estado.remaining = segundosRestantes();
    estado.running = false;
    desenhar();
  }

  function irPara(modo) {
    estado.mode = modo;
    estado.remaining = total();
    desenhar();
  }

  // descarta o cronômetro atual (e a sessão aberta no servidor, se houver)
  function descartar() {
    pararRelogio();
    estado.running = false;
    if (estado.sessionId !== null) {
      FF.api('POST', '/api/pomodoro/' + estado.sessionId + '/cancelar');
      estado.sessionId = null;
    }
  }

  function alternar() {
    if (estado.busy) return;
    if (estado.running) { pausar(); return; }

    if (estado.mode === 'foco' && estado.sessionId === null) {
      // primeiro "Iniciar" do foco: o servidor abre a sessão
      estado.busy = true;
      FF.api('POST', '/api/pomodoro/iniciar', { minutes: config.focus }).then(function (res) {
        estado.busy = false;
        if (!res.ok) {
          var erros = res.data.errors;
          FF.toast((erros && erros.minutes && erros.minutes[0]) ||
            res.data.error || 'Não foi possível iniciar a sessão.', 'danger');
          return;
        }
        estado.sessionId = res.data.session.id;
        rodar();
      });
    } else {
      rodar();
    }
  }

  function reiniciar() {
    descartar();
    estado.remaining = total();
    desenhar();
  }

  function trocarModo(modo) {
    descartar();
    irPara(modo);
  }

  /* ---- fim do tempo ---- */
  function terminar() {
    pararRelogio();
    estado.running = false;
    estado.remaining = 0;
    desenhar();

    if (estado.mode === 'descanso') {
      FF.toast('Descanso terminado. Hora de focar! 🎯', 'info');
      irPara('foco');
      return;
    }

    // foco concluído: o servidor confere o tempo e dá os pontos
    var id = estado.sessionId;
    estado.sessionId = null;
    estado.busy = true;
    FF.api('POST', '/api/pomodoro/' + id + '/concluir').then(function (res) {
      estado.busy = false;
      if (res.ok) {
        page.querySelector('[data-stat="sessions"]').textContent = res.data.today.sessions;
        page.querySelector('[data-stat="points"]').textContent = res.data.today.points;
        page.querySelector('[data-history]').innerHTML = res.data.history_html;
        FF.updatePoints(res.data.points_total);
        FF.toast('+' + res.data.points_awarded + ' pontos por sessão de foco! 🎯', 'points');
        irPara('descanso');
      } else {
        FF.toast(res.data.error || 'Não foi possível registrar a sessão.', 'danger');
        irPara('foco');
      }
    });
  }

  /* ---- eventos ---- */
  botaoPlay.addEventListener('click', alternar);
  botaoReset.addEventListener('click', reiniciar);
  abas.forEach(function (aba) {
    aba.addEventListener('click', function () { trocarModo(aba.dataset.modeTab); });
  });

  // avisa antes de fechar a aba com o cronômetro rodando (a sessão seria perdida)
  window.addEventListener('beforeunload', function (e) {
    if (estado.running) { e.preventDefault(); e.returnValue = ''; }
  });

  /* ---- configurações ---- */
  var rangeFoco = settingsForm.elements.focus;
  var rangePausa = settingsForm.elements.pause;
  var valorFoco = settingsForm.querySelector('[data-focus-value]');
  var valorPausa = settingsForm.querySelector('[data-break-value]');

  rangeFoco.addEventListener('input', function () { valorFoco.textContent = rangeFoco.value; });
  rangePausa.addEventListener('input', function () { valorPausa.textContent = rangePausa.value; });

  page.querySelector('[data-open-settings]').addEventListener('click', function () {
    rangeFoco.value = config.focus;
    rangePausa.value = config.pause;
    valorFoco.textContent = config.focus;
    valorPausa.textContent = config.pause;
    settingsModal.showModal();
  });

  settingsModal.querySelectorAll('[data-close]').forEach(function (b) {
    b.addEventListener('click', function () { settingsModal.close(); });
  });
  settingsModal.addEventListener('click', function (e) {
    if (e.target === settingsModal) settingsModal.close();
  });

  settingsForm.addEventListener('submit', function (e) {
    e.preventDefault();
    config = {
      focus: limitar(rangeFoco.value, limiteFoco.min, limiteFoco.max, 25),
      pause: limitar(rangePausa.value, 1, 30, 5)
    };
    try { localStorage.setItem(CHAVE, JSON.stringify(config)); } catch (err) { /* sem storage */ }
    descartar();                      // mudar a duração reinicia o cronômetro
    estado.remaining = total();
    desenhar();
    settingsModal.close();
  });

  desenhar();
})();
