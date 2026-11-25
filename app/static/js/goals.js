(function () {
  'use strict';
  var lista = document.querySelector('[data-goals-list]');
  if (!lista) return;

  function atualizarContadores(counts) {
    if (!counts) return;
    Object.keys(counts).forEach(function (chave) {
      document.querySelectorAll('[data-count="' + chave + '"]').forEach(function (el) {
        el.textContent = counts[chave];
      });
    });
  }

  lista.addEventListener('click', function (e) {
    var botao = e.target.closest('[data-claim]');
    if (!botao) return;
    var key = botao.closest('[data-goal-key]').dataset.goalKey;
    botao.disabled = true;
    FF.api('POST', '/api/metas/' + key + '/resgatar').then(function (res) {
      if (!res.ok) {
        botao.disabled = false;
        FF.toast(res.data.error || 'Não foi possível resgatar.', 'danger');
        return;
      }
      lista.innerHTML = res.data.html;
      atualizarContadores(res.data.counts);
      FF.updatePoints(res.data.points_total);
      FF.toast('+' + res.data.points_awarded + ' pontos! Meta evoluiu 🎯', 'points');
    });
  });
})();