/* FísicaFlow — comportamentos compartilhados (menu lateral, tema, toasts) */
(function () {
  'use strict';

  /* ---- Menu lateral no mobile ---- */
  var sidebar = document.querySelector('[data-sidebar]');
  var overlay = document.querySelector('[data-sidebar-overlay]');

  function setSidebar(open) {
    if (!sidebar) return;
    sidebar.classList.toggle('is-open', open);
    if (overlay) overlay.hidden = !open;
  }

  document.querySelectorAll('[data-sidebar-open]').forEach(function (btn) {
    btn.addEventListener('click', function () { setSidebar(true); });
  });
  document.querySelectorAll('[data-sidebar-close]').forEach(function (el) {
    el.addEventListener('click', function () { setSidebar(false); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setSidebar(false);
  });

  /* ---- Tema claro/escuro (lembra a escolha no navegador) ---- */
  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var root = document.documentElement;
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('ff-theme', next); } catch (err) { /* sem storage */ }
    });
  });

  /* ---- Toasts: somem sozinhos e podem ser fechados ---- */
  function dismiss(toast) {
    toast.classList.add('is-leaving');
    setTimeout(function () { toast.remove(); }, 260);
  }
  document.querySelectorAll('[data-toast]').forEach(function (toast) {
    var tempo = toast.classList.contains('toast-danger') ? 7000 : 4000;
    setTimeout(function () { dismiss(toast); }, tempo);
    var close = toast.querySelector('[data-toast-close]');
    if (close) close.addEventListener('click', function () { dismiss(toast); });
  });
  /* =====================================================================
     window.FF — utilidades para as telas que usam AJAX
       FF.api(metodo, url, corpo)  -> chama a API JSON (já envia o token CSRF)
       FF.toast(texto, tipo)       -> mostra um aviso (success, danger, info...)
     ===================================================================== */
  var FF = window.FF = window.FF || {};

  FF.api = function (metodo, url, corpo) {
    var meta = document.querySelector('meta[name="csrf-token"]');
    var opcoes = {
      method: metodo,
      credentials: 'same-origin',
      headers: {
        'Accept': 'application/json',
        'X-CSRFToken': meta ? meta.content : ''
      }
    };
    if (corpo !== undefined) {
      opcoes.headers['Content-Type'] = 'application/json';
      opcoes.body = JSON.stringify(corpo);
    }

    return fetch(url, opcoes)
      .then(function (res) {
        if (res.status === 401) {          // sessão expirou: volta para o login
          window.location.href = '/login';
        }
        return res.json().catch(function () {
          // resposta que não é JSON (ex.: token CSRF vencido = sessão expirada)
          return res.ok ? {} : {
            error: 'Sua sessão expirou. Recarregue a página e tente novamente.'
          };
        }).then(function (dados) {
          return { ok: res.ok, status: res.status, data: dados };
        });
      })
      .catch(function () {
        return { ok: false, status: 0, data: { error: 'Sem conexão com o servidor.' } };
      });
  };

  var ICONES_TOAST = {
    success: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    danger: '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    points: '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>'
  };

  /* FF.updatePoints(total) — atualiza o total de pontos em toda a tela
     (topo e barra lateral) com a contagem "subindo" do protótipo. */
  var semAnimacao = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  FF.updatePoints = function (novoTotal) {
    document.querySelectorAll('[data-points]').forEach(function (el) {
      var atual = parseInt(el.textContent, 10) || 0;
      if (semAnimacao || atual === novoTotal || !window.requestAnimationFrame) {
        el.textContent = novoTotal;
        return;
      }
      var inicio = null;
      var duracao = 700;
      function passo(agora) {
        if (inicio === null) inicio = agora;
        var p = Math.min((agora - inicio) / duracao, 1);
        el.textContent = Math.round(atual + (novoTotal - atual) * p);
        if (p < 1) window.requestAnimationFrame(passo);
      }
      window.requestAnimationFrame(passo);
    });
  };

  FF.toast = function (texto, tipo) {
    tipo = tipo || 'success';
    var pilha = document.querySelector('.toast-stack');
    if (!pilha) return;

    var toast = document.createElement('div');
    toast.className = 'toast toast-' + tipo;
    toast.setAttribute('role', 'status');

    var icone = ICONES_TOAST[tipo] || ICONES_TOAST.info;
    toast.innerHTML =
      '<svg class="icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" ' +
      'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + icone + '</svg>';

    var span = document.createElement('span');
    span.textContent = texto;               // textContent: nunca interpreta HTML
    toast.appendChild(span);

    pilha.appendChild(toast);
    setTimeout(function () { dismiss(toast); }, tipo === 'danger' ? 7000 : 3500);
  };
})();
