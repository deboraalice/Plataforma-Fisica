/* FísicaFlow — telas de login e cadastro */
(function () {
  'use strict';

  /* ---- Mostrar / ocultar senha ---- */
  document.querySelectorAll('[data-toggle-password]').forEach(function (btn) {
    var input = document.getElementById(btn.dataset.togglePassword);
    if (!input) return;
    btn.addEventListener('click', function () {
      var mostrar = input.type === 'password';
      input.type = mostrar ? 'text' : 'password';
      btn.classList.toggle('is-visible', mostrar);
      btn.setAttribute('aria-pressed', String(mostrar));
      btn.setAttribute('aria-label', mostrar ? 'Ocultar senha' : 'Mostrar senha');
    });
  });

  /* ---- Indicador de força da senha ---- */
  var meter = document.querySelector('[data-strength]');
  if (meter) {
    var senha = document.getElementById(meter.dataset.strength);
    var rotulo = meter.querySelector('.strength-label');
    var nomes = ['', 'Fraca', 'Razoável', 'Boa', 'Forte'];

    var avaliar = function () {
      var v = senha.value;
      meter.hidden = !v;
      if (!v) return;
      var pontos = [
        v.length >= 8,
        /[A-Z]/.test(v),
        /[0-9]/.test(v),
        /[^A-Za-z0-9]/.test(v)
      ].filter(Boolean).length;
      meter.dataset.score = pontos;
      rotulo.textContent = nomes[pontos] || 'Muito fraca';
    };
    senha.addEventListener('input', avaliar);
    avaliar();
  }

  /* ---- Aviso sobre e-mail institucional (IFRN) ---- */
  var email = document.querySelector('[data-ifrn-domains]');
  if (email) {
    var dominios = email.dataset.ifrnDomains.split(',');
    var ok = document.querySelector('[data-ifrn-ok]');
    var info = document.querySelector('[data-ifrn-info]');
    var campo = email.closest('.field');

    var checarEmail = function () {
      var v = email.value.trim().toLowerCase();
      var institucional = dominios.some(function (d) { return v.endsWith(d); });
      var digitando = v.indexOf('@') > 0 && !v.endsWith('@');
      ok.hidden = !institucional;
      info.hidden = institucional || !digitando;
      campo.classList.toggle('is-valid', institucional && !campo.classList.contains('has-error'));
    };
    email.addEventListener('input', checarEmail);
    checarEmail();
  }

  /* ---- Estado de carregamento ao enviar ---- */
  function restaurar(botao) {
    botao.disabled = false;
    botao.classList.remove('is-loading');
    if (botao.dataset.originalText) botao.textContent = botao.dataset.originalText;
  }

  document.querySelectorAll('form[data-loading-form]').forEach(function (form) {
    form.addEventListener('submit', function () {
      var botao = form.querySelector('[type="submit"]');
      if (!botao) return;
      botao.dataset.originalText = botao.textContent;
      botao.textContent = botao.dataset.loadingText || 'Enviando...';
      botao.classList.add('is-loading');
      // adia o disable para não cancelar o envio do formulário
      setTimeout(function () { botao.disabled = true; }, 0);
    });
    // botão "voltar" do navegador: volta ao estado normal
    window.addEventListener('pageshow', function () {
      var botao = form.querySelector('[type="submit"]');
      if (botao) restaurar(botao);
    });
  });
})();
