/* Acompanha reprodução contínua no YouTube e pede ao servidor a recompensa. */
(function () {
  'use strict';
  var frames = Array.prototype.slice.call(document.querySelectorAll('[data-youtube-watch]'));
  if (!frames.length) return;

  var timers = {};
  var completed = {};
  var requests = {};
  var statuses = {};
  function showStatus(id, message) {
    var status = statuses[id];
    if (!status) {
      var frame = document.querySelector('[data-resource-id="' + id + '"]');
      if (!frame) return;
      status = document.createElement('p');
      status.className = 'page-sub';
      frame.parentNode.insertAdjacentElement('afterend', status);
      statuses[id] = status;
    }
    status.textContent = message;
  }
  function report(player, id, ended) {
    if (completed[id]) return Promise.resolve();
    var position = player.getCurrentTime();
    var duration = player.getDuration();
    if (!duration) return Promise.resolve();
    var send = function () { return window.FF.api('POST', '/api/fisica/videos/' + id + '/progresso', {
      position: position,
      duration: duration,
      ended: !!ended
    }).then(function (res) {
      if (!res.ok) {
        if (ended) window.FF.toast(res.data.error || 'Não foi possível confirmar a conclusão. Tente novamente.', 'danger');
        return;
      }
      if (res.data.completed) {
        completed[id] = true;
        if (res.data.points_total !== undefined) window.FF.updatePoints(res.data.points_total);
        var message = res.data.already_awarded
          ? 'Vídeo concluído com sucesso! Você já recebeu os pontos deste vídeo.'
          : 'Vídeo concluído com sucesso! +' + res.data.awarded + ' pontos 🎉';
        window.FF.toast(message, 'success');
      } else if (ended) {
        window.FF.toast('Não ganhe pontos ao adiantar o vídeo. Assista até o final para concluir.', 'danger');
      }
    }); };
    requests[id] = (requests[id] || Promise.resolve()).then(send, send);
    return requests[id];
  }

  function initialize() {
    frames.forEach(function (frame) {
      var id = frame.getAttribute('data-resource-id');
      var player = new YT.Player(frame.id, {
        events: {
          onStateChange: function (event) {
            if (event.data === YT.PlayerState.PLAYING) {
              report(player, id, false);
              if (!timers[id]) timers[id] = window.setInterval(function () { report(player, id, false); }, 5000);
            } else {
              if (timers[id]) { window.clearInterval(timers[id]); timers[id] = null; }
              if (event.data === YT.PlayerState.ENDED) report(player, id, true);
              else if (event.data === YT.PlayerState.PAUSED) report(player, id, false);
            }
          },
          onError: function () { window.FF.toast('Não foi possível acompanhar este vídeo. Recarregue a página e tente novamente.', 'danger'); }
        }
      });
    });
  }

  window.onYouTubeIframeAPIReady = initialize;
  var script = document.createElement('script');
  script.src = 'https://www.youtube.com/iframe_api';
  document.head.appendChild(script);
}());
