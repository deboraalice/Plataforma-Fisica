/* FísicaFlow — tela de Cronograma (AJAX + JSON)
 *
 * Aqui a resposta da API traz o QUADRO inteiro já renderizado pelo Jinja
 * (grade da semana + lista por dia), porque criar ou editar um bloco muda a
 * posição de vários elementos. O JavaScript só troca o conteúdo do quadro.
 * Os modais de criar/editar/excluir ficam em crud.js (compartilhado).
 */
(function () {
  'use strict';

  var page = document.querySelector('[data-schedule-page]');
  if (!page) return;

  var board = page.querySelector('[data-board]');
  var subtitle = page.querySelector('[data-subtitle]');

  // dia mostrado na lista do mobile; começa em "hoje" (0 = segunda ... 6 = domingo)
  var diaAtivo = (new Date().getDay() + 6) % 7;

  function mostrarDia() {
    board.querySelectorAll('[data-day]').forEach(function (lista) {
      lista.hidden = Number(lista.dataset.day) !== diaAtivo;
    });
    board.querySelectorAll('[data-day-tab]').forEach(function (aba) {
      var ativa = Number(aba.dataset.dayTab) === diaAtivo;
      aba.classList.toggle('is-active', ativa);
      aba.setAttribute('aria-pressed', String(ativa));
    });
  }

  function atualizarQuadro(res) {
    board.innerHTML = res.data.html;
    mostrarDia();
    var n = res.data.counts.total;
    subtitle.textContent = n + (n === 1 ? ' bloco programado' : ' blocos programados');
  }

  /* ---- Modais de criar / editar / excluir ---- */
  var crud = FF.crud({
    page: page,
    endpoint: '/api/cronograma',
    texts: {
      newTitle: 'Novo horário', editTitle: 'Editar horário',
      create: 'Salvar', save: 'Salvar',
      created: 'Horário criado!', updated: 'Horário atualizado!', deleted: 'Horário excluído.'
    },
    fill: function (form, b) {
      form.elements.subject.value = b.subject;
      form.elements.weekday.value = String(b.weekday);
      form.elements.start_time.value = b.start_time;
      form.elements.end_time.value = b.end_time;
      form.querySelectorAll('[name="color"]').forEach(function (r) {
        r.checked = r.value === b.color;
      });
    },
    collect: function (form) {
      var cor = form.querySelector('[name="color"]:checked');
      return {
        subject: form.elements.subject.value,
        weekday: form.elements.weekday.value,
        start_time: form.elements.start_time.value,
        end_time: form.elements.end_time.value,
        color: cor ? cor.value : ''
      };
    },
    onSaved: atualizarQuadro,
    onDeleted: atualizarQuadro
  });

  /* ---- Cliques dentro do quadro (ele é recriado a cada atualização,
          por isso usamos um único ouvinte no elemento fixo) ---- */
  board.addEventListener('click', function (e) {
    var aba = e.target.closest('[data-day-tab]');
    if (aba) {
      diaAtivo = Number(aba.dataset.dayTab);
      mostrarDia();
      return;
    }

    var botao = e.target.closest('[data-action]');
    if (!botao) return;

    if (botao.dataset.action === 'edit') {
      crud.openForm(JSON.parse(botao.dataset.item));
    } else if (botao.dataset.action === 'delete') {
      crud.openDelete(botao.dataset.id);
    }
  });

  page.querySelector('[data-action="new"]').addEventListener('click', function () {
    crud.openForm(null);
    // já sugere o dia que está aberto na tela
    crud.form.elements.weekday.value = String(diaAtivo);
  });

  mostrarDia();
})();
