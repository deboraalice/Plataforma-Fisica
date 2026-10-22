/* FísicaFlow — modais de criar / editar / excluir (compartilhado)
 *
 * As telas de Tarefas, Metas e Cronograma têm o mesmo fluxo:
 *   abrir modal -> enviar JSON para a API -> mostrar erros por campo ->
 *   atualizar a tela -> fechar o modal (e o mesmo para excluir).
 * Esse arquivo guarda essa parte comum. Cada tela só informa o que é
 * específico dela (quais campos, qual URL, como atualizar a lista).
 *
 * Uso:
 *   var crud = FF.crud({
 *     page: elementoRaiz,            // contém os dois <dialog> e o formulário
 *     endpoint: '/api/tarefas',
 *     texts: { newTitle, editTitle, create, save, created, updated, deleted },
 *     fill: function (form, item) {},   // preenche o formulário ao editar
 *     collect: function (form) {},      // devolve o objeto JSON a enviar
 *     onSaved: function (res, editando) {},
 *     onDeleted: function (res, id) {}
 *   });
 *   crud.openForm(null)   // novo      | crud.openForm(item) // editar
 *   crud.openDelete(id)   // abre a confirmação de exclusão
 */
(function () {
  'use strict';

  var FF = window.FF = window.FF || {};

  FF.crud = function (cfg) {
    var page = cfg.page;
    var formModal = page.querySelector('[data-modal="form"]');
    var deleteModal = page.querySelector('[data-modal="delete"]');
    var form = formModal.querySelector('form');
    var formTitle = form.querySelector('[data-form-title]');
    var formError = form.querySelector('[data-form-error]');
    var submitBtn = form.querySelector('[data-submit]');
    var t = cfg.texts;

    var editandoId = null;    // null = criando um item novo
    var excluindoId = null;

    /* ---- abrir / fechar modais ---- */
    [formModal, deleteModal].forEach(function (modal) {
      modal.querySelectorAll('[data-close]').forEach(function (b) {
        b.addEventListener('click', function () { modal.close(); });
      });
      modal.addEventListener('click', function (e) {   // clique no fundo escuro
        if (e.target === modal) modal.close();
      });
    });

    /* ---- erros do formulário ---- */
    function limparErros() {
      formError.hidden = true;
      formError.textContent = '';
      form.querySelectorAll('[data-error-for]').forEach(function (p) {
        p.hidden = true;
        p.textContent = '';
      });
      form.querySelectorAll('.field.has-error').forEach(function (f) {
        f.classList.remove('has-error');
      });
    }

    function mostrarErros(erros) {
      var sobrou = [];
      Object.keys(erros).forEach(function (campo) {
        var alvo = form.querySelector('[data-error-for="' + campo + '"]');
        if (!alvo) { sobrou.push(erros[campo][0]); return; }
        alvo.textContent = erros[campo][0];
        alvo.hidden = false;
        alvo.closest('.field').classList.add('has-error');
      });
      if (sobrou.length) {
        formError.textContent = sobrou.join(' ');
        formError.hidden = false;
      }
      var primeiro = form.querySelector('.field.has-error .input');
      if (primeiro) primeiro.focus();
    }

    /* ---- criar / editar ---- */
    function openForm(item) {
      limparErros();
      form.reset();
      editandoId = item ? item.id : null;
      if (item) cfg.fill(form, item);

      formTitle.textContent = item ? t.editTitle : t.newTitle;
      submitBtn.textContent = item ? t.save : t.create;

      formModal.showModal();
      var primeiro = form.querySelector('.input');
      if (primeiro) primeiro.focus();
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      limparErros();

      var editando = editandoId !== null;
      var textoOriginal = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'Salvando...';

      var dados = cfg.collect(form);
      var req = editando
        ? FF.api('PUT', cfg.endpoint + '/' + editandoId, dados)
        : FF.api('POST', cfg.endpoint, dados);

      req.then(function (res) {
        submitBtn.disabled = false;
        submitBtn.textContent = textoOriginal;

        if (res.ok) {
          cfg.onSaved(res, editando);
          formModal.close();
          FF.toast(editando ? t.updated : t.created);
        } else if (res.data.errors) {
          mostrarErros(res.data.errors);
        } else {
          formError.textContent = res.data.error ||
            'Não foi possível salvar. Recarregue a página e tente novamente.';
          formError.hidden = false;
        }
      });
    });

    /* ---- excluir ---- */
    function openDelete(id) {
      excluindoId = id;
      deleteModal.showModal();
    }

    deleteModal.querySelector('[data-confirm-delete]').addEventListener('click', function (e) {
      var botao = e.currentTarget;
      var id = excluindoId;
      botao.disabled = true;
      FF.api('DELETE', cfg.endpoint + '/' + id).then(function (res) {
        botao.disabled = false;
        deleteModal.close();
        if (res.ok) {
          cfg.onDeleted(res, id);
          FF.toast(t.deleted);
        } else {
          FF.toast(res.data.error || 'Não foi possível excluir.', 'danger');
        }
      });
    });

    return { openForm: openForm, openDelete: openDelete, form: form };
  };
})();
