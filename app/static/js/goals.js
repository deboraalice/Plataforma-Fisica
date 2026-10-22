/* FísicaFlow — tela de Metas (AJAX + JSON)
 * Mesmo fluxo da tela de Tarefas: JavaScript -> JSON -> Flask -> JSON
 * (com o card já renderizado pelo Jinja) -> atualiza a tela.
 * Os modais de criar/editar/excluir ficam em crud.js (compartilhado).
 */
(function () {
  'use strict';

  var page = document.querySelector('[data-goals-page]');
  if (!page) return;

  var list = page.querySelector('[data-goal-list]');
  var empty = page.querySelector('[data-empty]');
  var filtroAtual = 'todas';

  var esperar = function (ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  };
  var semAnimacao = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- Lista: filtro, ordenação, contadores ---- */
  function cards() {
    return Array.prototype.slice.call(list.querySelectorAll('[data-goal-card]'));
  }

  function aplicarFiltro() {
    var visiveis = 0;
    cards().forEach(function (card) {
      var esconder = filtroAtual !== 'todas' && card.dataset.type !== filtroAtual;
      card.hidden = esconder;
      if (!esconder) visiveis++;
    });
    empty.hidden = visiveis > 0;
  }

  // mesma regra do servidor: em andamento primeiro (prazo mais próximo), concluídas no fim
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

  // devolve o card novo que entrou na lista
  function inserirOuSubstituir(html) {
    var modelo = document.createElement('template');
    modelo.innerHTML = html.trim();
    var novo = modelo.content.firstElementChild;
    var antigo = list.querySelector('[data-id="' + novo.dataset.id + '"]');
    novo.classList.add('is-new');
    if (antigo) { antigo.replaceWith(novo); } else { list.appendChild(novo); }
    ordenar();
    aplicarFiltro();
    return novo;
  }

  // confete leve ao concluir uma meta
  function confete(card) {
    if (semAnimacao) return;
    var cores = ['#4F46E5', '#06B6D4', '#F59E0B', '#10B981', '#8B5CF6'];
    var caixa = document.createElement('div');
    caixa.className = 'confetti';
    caixa.setAttribute('aria-hidden', 'true');
    for (var i = 0; i < 16; i++) {
      var p = document.createElement('span');
      p.style.left = (5 + Math.random() * 90) + '%';
      p.style.background = cores[i % cores.length];
      p.style.animationDelay = (Math.random() * 0.25) + 's';
      caixa.appendChild(p);
    }
    card.appendChild(caixa);
    setTimeout(function () { caixa.remove(); }, 1500);
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
    endpoint: '/api/metas',
    texts: {
      newTitle: 'Nova meta', editTitle: 'Editar meta',
      create: 'Criar meta', save: 'Salvar',
      created: 'Meta criada!', updated: 'Meta atualizada!', deleted: 'Meta excluída.'
    },
    fill: function (form, m) {
      form.elements.title.value = m.title;
      form.elements.type.value = m.type;
      form.elements.due_date.value = m.due_date;
    },
    collect: function (form) {
      return {
        title: form.elements.title.value,
        type: form.elements.type.value,
        due_date: form.elements.due_date.value
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
    var card = botao.closest('[data-goal-card]');
    var id = card.dataset.id;

    if (botao.dataset.action === 'edit') {
      crud.openForm(JSON.parse(card.dataset.goal));

    } else if (botao.dataset.action === 'delete') {
      crud.openDelete(id);

    } else if (botao.dataset.action === 'complete') {
      botao.disabled = true;
      card.classList.add('is-completing');       // animação sutil de conclusão

      // espera o servidor E a animação (600 ms) terminarem
      Promise.all([
        FF.api('PATCH', '/api/metas/' + id + '/concluir'),
        esperar(semAnimacao ? 0 : 600)
      ]).then(function (resultados) {
        var res = resultados[0];
        if (res.ok) {
          var novo = inserirOuSubstituir(res.data.html);
          atualizarContadores(res.data.counts);
          confete(novo);
          FF.toast('Meta concluída! 🎉');
        } else {
          botao.disabled = false;
          card.classList.remove('is-completing');
          FF.toast(res.data.error || 'Não foi possível concluir a meta.', 'danger');
        }
      });
    }
  });

  page.querySelector('[data-action="new"]').addEventListener('click', function () {
    crud.openForm(null);
  });

  aplicarFiltro();
})();
