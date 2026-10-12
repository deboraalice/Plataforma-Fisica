/* FísicaFlow — tela de Tarefas (AJAX + JSON)
 *
 * Fluxo de cada ação:
 *   1. o JavaScript envia JSON para a API (FF.api -> fetch);
 *   2. o Flask valida, grava no banco (SQLAlchemy) e responde em JSON;
 *   3. a resposta traz o card já renderizado pelo Jinja ("html") e os
 *      contadores ("counts"), e o JavaScript só atualiza a tela.
 *
 * Os modais de criar/editar/excluir ficam em crud.js (compartilhado).
 */
(function () {
  'use strict';

  var page = document.querySelector('[data-tasks-page]');
  if (!page) return;

  var list = page.querySelector('[data-task-list]');
  var empty = page.querySelector('[data-empty]');
  var filtroAtual = 'todas';

  /* ---- Lista: filtro, ordenação, contadores ---- */
  function cards() {
    return Array.prototype.slice.call(list.querySelectorAll('[data-task-card]'));
  }

  function aplicarFiltro() {
    var visiveis = 0;
    cards().forEach(function (card) {
      var esconder = filtroAtual !== 'todas' && card.dataset.status !== filtroAtual;
      card.hidden = esconder;
      if (!esconder) visiveis++;
    });
    empty.hidden = visiveis > 0;
  }

  // mesma regra do servidor: abertas primeiro (prazo mais próximo), concluídas no fim
  function ordenar() {
    cards()
      .sort(function (a, b) {
        var feitaA = a.dataset.status === 'concluida';
        var feitaB = b.dataset.status === 'concluida';
        if (feitaA !== feitaB) return feitaA ? 1 : -1;
        if (a.dataset.due !== b.dataset.due) return a.dataset.due < b.dataset.due ? -1 : 1;
        return Number(a.dataset.id) - Number(b.dataset.id);
      })
      .forEach(function (card) { list.appendChild(card); });
  }

  function atualizarContadores(counts) {
    if (!counts) return;
    page.querySelectorAll('[data-count]').forEach(function (el) {
      var valor = counts[el.dataset.count];
      if (valor !== undefined) el.textContent = valor;
    });
  }

  function inserirOuSubstituir(html) {
    var modelo = document.createElement('template');
    modelo.innerHTML = html.trim();
    var novo = modelo.content.firstElementChild;
    var antigo = list.querySelector('[data-id="' + novo.dataset.id + '"]');
    novo.classList.add('is-new');
    if (antigo) { antigo.replaceWith(novo); } else { list.appendChild(novo); }
    ordenar();
    aplicarFiltro();
  }

  page.querySelectorAll('[data-filter]').forEach(function (botao) {
    botao.addEventListener('click', function () {
      filtroAtual = botao.dataset.filter;
      page.querySelectorAll('[data-filter]').forEach(function (b) {
        var ativo = b === botao;
        b.classList.toggle('is-active', ativo);
        b.setAttribute('aria-pressed', String(ativo));
      });
      aplicarFiltro();
    });
  });

  /* ---- Modais de criar / editar / excluir ---- */
  var crud = FF.crud({
    page: page,
    endpoint: '/api/tarefas',
    texts: {
      newTitle: 'Nova tarefa', editTitle: 'Editar tarefa',
      create: 'Criar tarefa', save: 'Salvar',
      created: 'Tarefa criada!', updated: 'Tarefa atualizada!', deleted: 'Tarefa excluída.'
    },
    fill: function (form, t) {
      form.elements.title.value = t.title;
      form.elements.description.value = t.description;
      form.elements.subject.value = t.subject;
      form.elements.due_date.value = t.due_date;
      form.elements.priority.value = t.priority;
      form.elements.status.value = t.status;
    },
    collect: function (form) {
      return {
        title: form.elements.title.value,
        description: form.elements.description.value,
        subject: form.elements.subject.value,
        due_date: form.elements.due_date.value,
        priority: form.elements.priority.value,
        status: form.elements.status.value
      };
    },
    onSaved: function (res) {
      inserirOuSubstituir(res.data.html);
      atualizarContadores(res.data.counts);
    },
    onDeleted: function (res, id) {
      var card = list.querySelector('[data-id="' + id + '"]');
      if (card) card.remove();
      atualizarContadores(res.data.counts);
      aplicarFiltro();
    }
  });

  /* ---- Ações em cada card ---- */
  list.addEventListener('click', function (e) {
    var botao = e.target.closest('[data-action]');
    if (!botao) return;
    var card = botao.closest('[data-task-card]');

    if (botao.dataset.action === 'edit') {
      crud.openForm(JSON.parse(card.dataset.task));

    } else if (botao.dataset.action === 'delete') {
      crud.openDelete(card.dataset.id);

    } else if (botao.dataset.action === 'toggle') {
      botao.disabled = true;
      FF.api('PATCH', '/api/tarefas/' + card.dataset.id + '/concluir').then(function (res) {
        if (res.ok) {
          inserirOuSubstituir(res.data.html);
          atualizarContadores(res.data.counts);
          FF.toast(res.data.task.status === 'concluida'
            ? 'Tarefa concluída! 🎉' : 'Tarefa reaberta.', 'success');
        } else {
          botao.disabled = false;
          FF.toast(res.data.error || 'Não foi possível atualizar a tarefa.', 'danger');
        }
      });
    }
  });

  page.querySelector('[data-action="new"]').addEventListener('click', function () {
    crud.openForm(null);
  });

  aplicarFiltro();
})();
