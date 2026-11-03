(function () {
  'use strict';

  var root = document.querySelector('[data-simulator]');
  if (!root) return;

  var canvas = root.querySelector('[data-sim-canvas]');
  var context = canvas.getContext('2d');
  var fieldsHost = root.querySelector('[data-sim-fields]');
  var resultsHost = root.querySelector('[data-sim-results]');
  var explanationHost = root.querySelector('[data-sim-explanation]');
  var statusHost = root.querySelector('[data-sim-status]');
  var formulaHost = root.querySelector('[data-sim-formula]');
  var tipHost = root.querySelector('[data-sim-tip]');
  var action = root.querySelector('[data-sim-action]');
  var reset = root.querySelector('[data-sim-reset]');
  var actionLabel = root.querySelector('[data-sim-action-label]');
  var slug = root.dataset.simulator;
  var animationId = null;
  var animationStart = 0;

  function number(value) { return Number(value) || 0; }
  function fixed(value, decimals) {
    return Number(value).toLocaleString('pt-BR', {
      minimumFractionDigits: decimals || 0,
      maximumFractionDigits: decimals || 0
    });
  }
  function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }

  function palette() {
    var style = getComputedStyle(document.documentElement);
    return {
      primary: style.getPropertyValue('--primary').trim() || '#4F46E5',
      cyan: style.getPropertyValue('--cyan').trim() || '#06B6D4',
      success: style.getPropertyValue('--success').trim() || '#10B981',
      warning: style.getPropertyValue('--warning').trim() || '#F59E0B',
      text: style.getPropertyValue('--text').trim() || '#0F172A',
      muted: style.getPropertyValue('--muted').trim() || '#64748B',
      card: style.getPropertyValue('--card').trim() || '#FFFFFF',
      border: style.getPropertyValue('--border').trim() || '#E2E8F0'
    };
  }

  function line(ctx, x1, y1, x2, y2, color, width, dash) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = color;
    ctx.lineWidth = width || 2;
    if (dash) ctx.setLineDash(dash);
    ctx.stroke();
    ctx.restore();
  }

   function arrow(ctx, x1, y1, x2, y2, color, label) {
    line(ctx, x1, y1, x2, y2, color, 3);
    var angle = Math.atan2(y2 - y1, x2 - x1);
    ctx.save();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - 10 * Math.cos(angle - Math.PI / 6), y2 - 10 * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(x2 - 10 * Math.cos(angle + Math.PI / 6), y2 - 10 * Math.sin(angle + Math.PI / 6));
    ctx.fill();
    if (label) {
      ctx.font = '600 12px Inter, sans-serif';
      ctx.fillText(label, (x1 + x2) / 2 - 8, (y1 + y2) / 2 - 8);
    }
    ctx.restore();
  }

  function label(ctx, text, x, y, color, align) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.font = '600 12px Inter, sans-serif';
    ctx.textAlign = align || 'left';
    ctx.fillText(text, x, y);
    ctx.restore();
  }

  function roundedRect(ctx, x, y, width, height, radius, color) {
    ctx.save();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, radius);
    ctx.fill();
    ctx.restore();
  }

  var configs = {
    cinematica: {
      formula: 'v = v₀ + a·t',
      tip: 'Exemplo: compare uma arrancada suave (1 m/s²) com uma mais intensa (4 m/s²).',
      fields: [
        ['v0', 'Velocidade inicial', 0, 30, 5, 1, 'm/s'],
        ['a', 'Aceleração', -3, 6, 2, 0.5, 'm/s²'],
        ['t', 'Tempo observado', 1, 15, 6, 1, 's']
      ],
      calculate: function (v) {
        var velocity = Math.max(0, v.v0 + v.a * v.t);
        var distance = Math.max(0, v.v0 * v.t + .5 * v.a * v.t * v.t);
        return {
          status: velocity > v.v0 ? 'O carro ganhou velocidade' : velocity < v.v0 ? 'O carro desacelerou' : 'Velocidade constante',
          results: [['Velocidade final', fixed(velocity, 1) + ' m/s'], ['Em km/h', fixed(velocity * 3.6, 1) + ' km/h'], ['Distância', fixed(distance, 1) + ' m']],
          explanation: 'Com aceleração constante, a velocidade muda a mesma quantidade a cada segundo. A área acumulada sob essa mudança determina a distância percorrida.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var roadY = h * .7;
        ctx.fillStyle = '#93C5FD'; ctx.fillRect(0, 0, w, roadY);
        ctx.fillStyle = '#BBF7D0'; ctx.fillRect(0, roadY - 28, w, 28);
        ctx.fillStyle = '#334155'; ctx.fillRect(0, roadY, w, h - roadY);
        for (var x = -40; x < w; x += 90) line(ctx, x, roadY + 48, x + 48, roadY + 48, '#F8FAFC', 4);
        var speed = clamp((v.v0 + Math.max(v.a, 0) * v.t) / 50, .08, 1);
        var carX = 24 + p * (w - 110) * speed;
        roundedRect(ctx, carX, roadY - 36, 76, 30, 8, c.primary);
        roundedRect(ctx, carX + 14, roadY - 52, 43, 21, 8, c.cyan);
        [carX + 17, carX + 60].forEach(function (cx) {
          ctx.beginPath(); ctx.arc(cx, roadY - 4, 9, 0, Math.PI * 2); ctx.fillStyle = '#0F172A'; ctx.fill();
        });
        label(ctx, fixed(v.v0 + v.a * v.t, 1) + ' m/s', carX + 38, roadY - 65, c.text, 'center');
      }

      },
    dinamica: {
      formula: 'ΣF = m·a',
      tip: 'O atrito sempre atua no sentido oposto ao movimento do carrinho.',
      fields: [
        ['mass', 'Massa do carrinho', 5, 80, 25, 5, 'kg'],
        ['force', 'Força aplicada', 0, 200, 100, 10, 'N'],
        ['friction', 'Força de atrito', 0, 100, 30, 5, 'N']
      ],
      calculate: function (v) {
        var net = Math.max(0, v.force - v.friction);
        var acceleration = net / v.mass;
        return {
          status: net ? 'O carrinho está acelerando' : 'As forças não movem o carrinho',
          results: [['Força resultante', fixed(net, 0) + ' N'], ['Aceleração', fixed(acceleration, 2) + ' m/s²'], ['Peso aproximado', fixed(v.mass * 9.8, 0) + ' N']],
          explanation: 'A força resultante é a força aplicada menos o atrito. Para a mesma força, um carrinho com mais massa apresenta menor aceleração.'
        };
     },
      draw: function (ctx, w, h, v, p, c) {
        var floor = h * .73;
        line(ctx, 0, floor, w, floor, c.border, 3);
        var net = Math.max(0, v.force - v.friction);
        var x = 40 + p * (w - 180) * clamp(net / 150, 0, 1);
        ctx.strokeStyle = c.text; ctx.lineWidth = 5; ctx.strokeRect(x, floor - 72, 100, 55);
        line(ctx, x + 100, floor - 72, x + 122, floor - 104, c.text, 5);
        [x + 22, x + 82].forEach(function (cx) {
          ctx.beginPath(); ctx.arc(cx, floor - 8, 10, 0, Math.PI * 2); ctx.fillStyle = c.text; ctx.fill();
        });
        arrow(ctx, x + 105, floor - 48, x + 105 + Math.min(v.force, 150) * .65, floor - 48, c.success, 'F');
        if (v.friction) arrow(ctx, x, floor - 23, x - Math.min(v.friction, 80) * .6, floor - 23, c.warning, 'atrito');
        label(ctx, v.mass + ' kg', x + 50, floor - 41, c.text, 'center');
      }
   },
    'energia-trabalho': {
      formula: 'Eₚ = m·g·h',
      tip: 'Desconsidere o atrito para observar a conservação da energia mecânica.',
      fields: [
        ['mass', 'Massa do carrinho', 100, 800, 300, 50, 'kg'],
        ['height', 'Altura inicial', 5, 40, 22, 1, 'm'],
        ['currentHeight', 'Altura observada', 0, 40, 6, 1, 'm']
      ],
      calculate: function (v) {
        var current = Math.min(v.currentHeight, v.height);
        var total = v.mass * 9.8 * v.height;
        var potential = v.mass * 9.8 * current;
        var kinetic = Math.max(0, total - potential);
        var speed = Math.sqrt(2 * kinetic / v.mass);
        return {
          status: current < v.height ? 'Energia potencial virou movimento' : 'Carrinho no ponto mais alto',
          results: [['Energia total', fixed(total / 1000, 1) + ' kJ'], ['Energia cinética', fixed(kinetic / 1000, 1) + ' kJ'], ['Velocidade', fixed(speed, 1) + ' m/s']],
          explanation: 'Ao descer, o carrinho perde energia potencial gravitacional e ganha energia cinética. Sem atrito, a soma das duas permanece constante.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var base = h * .82, top = h * .17;
        ctx.beginPath(); ctx.moveTo(20, top); ctx.bezierCurveTo(w * .3, top, w * .35, base, w * .58, base); ctx.bezierCurveTo(w * .76, base, w * .72, h * .48, w - 20, h * .48);
        ctx.strokeStyle = c.text; ctx.lineWidth = 5; ctx.stroke();
        var t = p, x = 20 + t * (w * .56), y = top + (base - top) * (t * t * (3 - 2 * t));
        roundedRect(ctx, x - 18, y - 18, 38, 20, 5, c.primary);
        [x - 10, x + 12].forEach(function (cx) { ctx.beginPath(); ctx.arc(cx, y + 4, 5, 0, 7); ctx.fillStyle = c.text; ctx.fill(); });
        arrow(ctx, w - 54, base, w - 54, top, c.cyan, 'h');
        label(ctx, v.height + ' m', w - 45, (base + top) / 2, c.text);
      }
    },
    termodinamica: {
      formula: 'Q = m·c·ΔT',
      tip: 'Foi considerada uma chaleira ideal; na vida real parte da energia aquece o ambiente.',
      fields: [
        ['mass', 'Quantidade de água', .2, 2, 1, .1, 'kg'],
        ['initial', 'Temperatura inicial', 5, 50, 20, 1, '°C'],
        ['final', 'Temperatura desejada', 30, 100, 90, 1, '°C'],
        ['power', 'Potência do aquecedor', 500, 2500, 1500, 100, 'W']
      ],
      calculate: function (v) {
        var delta = Math.max(0, v.final - v.initial);
        var energy = v.mass * 4200 * delta;
        var seconds = energy / v.power;
        return {
          status: delta ? 'A água está recebendo calor' : 'Não há variação de temperatura',
          results: [['Variação térmica', fixed(delta, 0) + ' °C'], ['Energia necessária', fixed(energy / 1000, 1) + ' kJ'], ['Tempo ideal', fixed(seconds / 60, 1) + ' min']],
          explanation: 'Quanto maior a massa de água ou a variação de temperatura, mais energia é necessária. Um aquecedor mais potente entrega essa energia em menos tempo.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var cx = w / 2, base = h * .78, potW = Math.min(230, w * .5);
        roundedRect(ctx, cx - potW / 2, base - 135, potW, 135, 16, '#64748B');
        ctx.fillStyle = '#38BDF8'; ctx.fillRect(cx - potW / 2 + 12, base - 95, potW - 24, 83);
        var tempRatio = clamp((v.initial + (v.final - v.initial) * p) / 100, 0, 1);
        ctx.fillStyle = 'rgba(239,68,68,' + (.15 + tempRatio * .55) + ')'; ctx.fillRect(cx - potW / 2 + 12, base - 95, potW - 24, 83);
        for (var i = 0; i < 3; i++) {
          ctx.beginPath(); ctx.moveTo(cx - 55 + i * 55, base - 150); ctx.bezierCurveTo(cx - 75 + i * 55, base - 180, cx - 35 + i * 55, base - 200, cx - 55 + i * 55, base - 230);
          ctx.strokeStyle = c.muted; ctx.lineWidth = 3; ctx.stroke();
        }
        label(ctx, fixed(v.initial + (v.final - v.initial) * p, 0) + ' °C', cx, base - 48, '#FFFFFF', 'center');
      }
    },
    'ondas-som': {
      formula: 'v = λ·f',
      tip: 'A frequência define o tom; a amplitude está relacionada à intensidade percebida.',
      fields: [
        ['frequency', 'Frequência', 100, 1200, 440, 10, 'Hz'],
        ['amplitude', 'Amplitude', 10, 100, 55, 5, '%'],
        ['speed', 'Velocidade do som', 300, 360, 343, 1, 'm/s']
      ],
      calculate: function (v) {
        var wavelength = v.speed / v.frequency;
        return {
          status: v.frequency < 300 ? 'Som grave' : v.frequency > 800 ? 'Som agudo' : 'Som de frequência média',
          results: [['Comprimento de onda', fixed(wavelength, 2) + ' m'], ['Período', fixed(1000 / v.frequency, 2) + ' ms'], ['Frequência', fixed(v.frequency, 0) + ' Hz']],
          explanation: 'Ao aumentar a frequência, mais oscilações cabem no mesmo intervalo e o comprimento de onda diminui. A velocidade no mesmo meio permanece praticamente constante.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var center = h / 2, cycles = 2 + (v.frequency - 100) / 190, amp = (h * .32) * v.amplitude / 100;
        ctx.fillStyle = c.text;
        ctx.beginPath(); ctx.moveTo(28, center - 50); ctx.lineTo(75, center - 26); ctx.lineTo(75, center + 26); ctx.lineTo(28, center + 50); ctx.closePath(); ctx.fill();
        ctx.beginPath();
        for (var x = 80; x <= w; x += 2) {
          var y = center + Math.sin((x / w * cycles + p * 2) * Math.PI * 2) * amp;
          if (x === 80) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = c.cyan; ctx.lineWidth = 4; ctx.stroke();
        line(ctx, 80, center, w, center, c.border, 1, [4, 5]);
      }
    },
    optica: {
      formula: '1/f = 1/p + 1/p′',
      tip: 'Use uma distância do objeto maior que a focal para formar uma imagem real.',
      fields: [
        ['focal', 'Distância focal', 5, 25, 12, 1, 'cm'],
        ['object', 'Distância do objeto', 8, 60, 35, 1, 'cm'],
        ['height', 'Altura do objeto', 2, 12, 8, 1, 'cm']
      ],
      calculate: function (v) {
        var denominator = (1 / v.focal) - (1 / v.object);
        var image = Math.abs(denominator) < .001 ? Infinity : 1 / denominator;
        var magnification = image === Infinity ? Infinity : -image / v.object;
        var type = image > 0 ? 'real e invertida' : 'virtual e direita';
        return {
          status: image === Infinity ? 'Raios emergem paralelos' : 'Imagem ' + type,
          results: [['Posição da imagem', image === Infinity ? '∞' : fixed(Math.abs(image), 1) + ' cm'], ['Ampliação', magnification === Infinity ? '∞' : fixed(Math.abs(magnification), 2) + '×'], ['Orientação', image > 0 ? 'Invertida' : 'Direita']],
          explanation: 'A lente convergente desvia os raios. Quando o objeto está além do foco, eles se cruzam e formam uma imagem real e invertida do outro lado.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var axis = h / 2, lensX = w / 2, scale = Math.min(6, w / 110), objectX = lensX - v.object * scale;
        line(ctx, 18, axis, w - 18, axis, c.border, 2);
        ctx.beginPath(); ctx.ellipse(lensX, axis, 13, h * .38, 0, 0, Math.PI * 2); ctx.fillStyle = 'rgba(6,182,212,.25)'; ctx.fill(); ctx.strokeStyle = c.cyan; ctx.lineWidth = 3; ctx.stroke();
        arrow(ctx, objectX, axis, objectX, axis - v.height * scale, c.primary, 'objeto');
        var denominator = 1 / v.focal - 1 / v.object, image = Math.abs(denominator) < .001 ? 999 : 1 / denominator;
        var imageX = clamp(lensX + image * scale, lensX + 20, w - 25);
        var imageH = clamp(v.height * Math.abs(image / v.object) * scale, 8, h * .35);
        line(ctx, objectX, axis - v.height * scale, lensX, axis - v.height * scale, c.warning, 2);
        line(ctx, lensX, axis - v.height * scale, imageX, axis + imageH, c.warning, 2);
        line(ctx, objectX, axis - v.height * scale, imageX, axis + imageH, c.success, 2);
        if (image > 0) arrow(ctx, imageX, axis, imageX, axis + imageH, c.success, 'imagem');
        [lensX - v.focal * scale, lensX + v.focal * scale].forEach(function (x) { ctx.beginPath(); ctx.arc(x, axis, 4, 0, 7); ctx.fillStyle = c.text; ctx.fill(); });
      }
    },
     eletricidade: {
      formula: 'U = R·i',
      tip: 'Não monte circuitos diretamente na tomada. Este experimento é apenas virtual.',
      fields: [
        ['voltage', 'Tensão da fonte', 1, 24, 12, 1, 'V'],
        ['resistance', 'Resistência da lâmpada', 2, 50, 10, 1, 'Ω']
      ],
      calculate: function (v) {
        var current = v.voltage / v.resistance, power = v.voltage * current, energy = power * 5 / 1000;
        return {
          status: power > 20 ? 'Lâmpada com brilho intenso' : power > 5 ? 'Lâmpada acesa' : 'Lâmpada com brilho fraco',
          results: [['Corrente', fixed(current, 2) + ' A'], ['Potência', fixed(power, 1) + ' W'], ['Energia em 5 h', fixed(energy, 2) + ' kWh']],
          explanation: 'Pela Lei de Ohm, aumentar a tensão eleva a corrente; aumentar a resistência a reduz. O brilho foi representado pela potência elétrica dissipada.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var cx = w / 2, cy = h / 2, power = v.voltage * v.voltage / v.resistance, glow = clamp(power / 40, .08, 1);
        ctx.save(); ctx.shadowColor = '#FBBF24'; ctx.shadowBlur = 70 * glow;
        ctx.beginPath(); ctx.arc(cx, cy - 30, 58, 0, Math.PI * 2); ctx.fillStyle = 'rgba(251,191,36,' + (.16 + glow * .72) + ')'; ctx.fill(); ctx.restore();
        ctx.beginPath(); ctx.arc(cx, cy - 30, 58, 0, Math.PI * 2); ctx.strokeStyle = c.warning; ctx.lineWidth = 4; ctx.stroke();
        line(ctx, cx - 22, cy + 27, cx - 22, cy + 75, c.text, 5); line(ctx, cx + 22, cy + 27, cx + 22, cy + 75, c.text, 5);
        line(ctx, cx - 22, cy + 75, 55, cy + 75, c.text, 4); line(ctx, cx + 22, cy + 75, w - 55, cy + 75, c.text, 4);
        line(ctx, 55, cy + 75, 55, cy - 100, c.text, 4); line(ctx, w - 55, cy + 75, w - 55, cy - 100, c.text, 4);
        line(ctx, 55, cy - 100, w - 55, cy - 100, c.text, 4);
        line(ctx, 42, cy - 75, 68, cy - 75, c.primary, 4); line(ctx, 48, cy - 62, 62, cy - 62, c.primary, 4);
        label(ctx, v.voltage + ' V', 80, cy - 66, c.primary);
      }
    },
    magnetismo: {
      formula: 'B ∝ N·i / L',
      tip: 'Em um eletroímã real, o núcleo de ferro também aumenta muito o campo.',
      fields: [
        ['turns', 'Número de espiras', 20, 200, 100, 10, 'espiras'],
        ['current', 'Corrente elétrica', .1, 5, 2, .1, 'A'],
        ['length', 'Comprimento da bobina', 5, 30, 15, 1, 'cm']
      ],
      calculate: function (v) {
        var relative = v.turns * v.current / v.length;
        return {
          status: relative > 25 ? 'Campo magnético intenso' : relative > 8 ? 'Campo magnético moderado' : 'Campo magnético fraco',
          results: [['Intensidade relativa', fixed(relative, 1)], ['Ampère-espiras', fixed(v.turns * v.current, 0) + ' A·e'], ['Comprimento', fixed(v.length, 0) + ' cm']],
          explanation: 'Mais corrente e mais espiras reforçam o campo magnético da bobina. Aumentar o comprimento espalha as espiras e reduz a intensidade interna.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var cx = w / 2, cy = h / 2, coilW = Math.min(280, w * .56), strength = clamp(v.turns * v.current / v.length / 35, .1, 1);
        roundedRect(ctx, cx - coilW / 2, cy - 34, coilW, 68, 8, '#64748B');
        var visibleTurns = Math.round(8 + v.turns / 20);
        for (var i = 0; i < visibleTurns; i++) {
          var x = cx - coilW / 2 + (i + .5) * coilW / visibleTurns;
          ctx.beginPath(); ctx.ellipse(x, cy, 10, 49, 0, 0, Math.PI * 2); ctx.strokeStyle = '#F97316'; ctx.lineWidth = 3; ctx.stroke();
        }
        for (var j = 1; j <= 3; j++) {
          ctx.beginPath(); ctx.ellipse(cx, cy, coilW / 2 + j * 28, 45 + j * 24, 0, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(79,70,229,' + strength * (1 - j * .18) + ')'; ctx.lineWidth = 3; ctx.stroke();
        }
        label(ctx, 'N', cx - coilW / 2 + 18, cy + 5, '#FFFFFF', 'center'); label(ctx, 'S', cx + coilW / 2 - 18, cy + 5, '#FFFFFF', 'center');
      }
    },
    hidrostatica: {
      formula: 'E = ρ·g·V',
      tip: 'A pressão aumenta com a profundidade, mesmo que o objeto tenha o mesmo tamanho.',
      fields: [
        ['depth', 'Profundidade', 0, 10, 3, .5, 'm'],
        ['density', 'Densidade do líquido', 700, 1300, 1000, 50, 'kg/m³'],
        ['volume', 'Volume do objeto', .01, .2, .08, .01, 'm³'],
        ['mass', 'Massa do objeto', 5, 200, 60, 5, 'kg']
      ],
      calculate: function (v) {
        var pressure = v.density * 9.8 * v.depth, buoyancy = v.density * 9.8 * v.volume, weight = v.mass * 9.8;
        return {
          status: buoyancy > weight ? 'O objeto tende a subir' : buoyancy < weight ? 'O objeto tende a afundar' : 'O objeto fica em equilíbrio',
          results: [['Pressão', fixed(pressure / 1000, 1) + ' kPa'], ['Empuxo', fixed(buoyancy, 0) + ' N'], ['Peso', fixed(weight, 0) + ' N']],
          explanation: 'O empuxo equivale ao peso do líquido deslocado. Se ele superar o peso do objeto, a força resultante aponta para cima e o objeto sobe.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var surface = h * .2;
        ctx.fillStyle = 'rgba(14,165,233,.42)'; ctx.fillRect(0, surface, w, h - surface);
        for (var x = 0; x < w; x += 35) {
          ctx.beginPath(); ctx.arc(x + p * 35, surface, 18, Math.PI, 0); ctx.strokeStyle = c.cyan; ctx.lineWidth = 2; ctx.stroke();
        }
        var y = surface + clamp(v.depth / 10, 0, 1) * (h - surface - 70);
        var size = 35 + clamp(v.volume / .2, 0, 1) * 30;
        roundedRect(ctx, w / 2 - size / 2, y - size / 2, size, size, 8, c.primary);
        var buoyancy = v.density * v.volume, rises = buoyancy >= v.mass;
        arrow(ctx, w / 2, y - size / 2, w / 2, y - size / 2 - 65 * clamp(buoyancy / 150, .25, 1), c.success, 'E');
        arrow(ctx, w / 2, y + size / 2, w / 2, y + size / 2 + 65 * clamp(v.mass / 150, .25, 1), c.warning, 'P');
        label(ctx, rises ? 'tende a subir' : 'tende a afundar', w / 2, h - 24, c.text, 'center');
      }
    },
    gravitacao: {
      formula: 'g = G·M / r²',
      tip: 'Massa não muda de planeta para planeta; peso é que depende da gravidade local.',
      fields: [
        ['world', 'Astro', 'select', [['terra', 'Terra'], ['lua', 'Lua'], ['marte', 'Marte'], ['jupiter', 'Júpiter']], 'terra'],
        ['mass', 'Massa da pessoa', 20, 150, 65, 1, 'kg'],
        ['altitude', 'Altitude', 0, 1000, 100, 25, 'km']
      ],
      calculate: function (v) {
        var worlds = {
          terra: [9.81, 6371, 5.972e24, 'Terra'],
          lua: [1.62, 1737, 7.342e22, 'Lua'],
          marte: [3.71, 3389, 6.417e23, 'Marte'],
          jupiter: [24.79, 69911, 1.898e27, 'Júpiter']
        };
        var world = worlds[v.world], g = world[0] * Math.pow(world[1] / (world[1] + v.altitude), 2);
        var orbital = Math.sqrt(6.674e-11 * world[2] / ((world[1] + v.altitude) * 1000));
        return {
          status: 'Explorando ' + world[3],
          results: [['Gravidade local', fixed(g, 2) + ' m/s²'], ['Seu peso', fixed(v.mass * g, 0) + ' N'], ['Velocidade orbital', fixed(orbital / 1000, 2) + ' km/s']],
          explanation: 'A gravidade diminui com a distância ao centro do astro. Sua massa permanece igual, mas o peso muda porque é o produto da massa pela gravidade local.'
        };
      },
      draw: function (ctx, w, h, v, p, c) {
        var colors = { terra: '#2563EB', lua: '#94A3B8', marte: '#EA580C', jupiter: '#D97706' };
        var radius = Math.min(w, h) * .2, cx = w / 2, cy = h / 2, orbit = radius + 65 + v.altitude / 18;
        ctx.fillStyle = '#070B24'; ctx.fillRect(0, 0, w, h);
        for (var i = 0; i < 45; i++) { ctx.fillStyle = 'rgba(255,255,255,' + (.2 + (i % 4) * .18) + ')'; ctx.fillRect((i * 83) % w, (i * 47) % h, 2, 2); }
        ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.fillStyle = colors[v.world]; ctx.fill();
        ctx.beginPath(); ctx.arc(cx, cy, Math.min(orbit, Math.min(w, h) * .45), 0, Math.PI * 2); ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.setLineDash([5, 6]); ctx.stroke(); ctx.setLineDash([]);
        var angle = p * Math.PI * 2, r = Math.min(orbit, Math.min(w, h) * .45);
        ctx.beginPath(); ctx.arc(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r, 7, 0, Math.PI * 2); ctx.fillStyle = '#F8FAFC'; ctx.fill();
      }
    }
  };
var config = configs[slug];
  if (!config) return;

  function createFields() {
    fieldsHost.innerHTML = '';
    config.fields.forEach(function (field) {
      var wrapper = document.createElement('div');
      wrapper.className = 'simulator-field';
      if (field[2] === 'select') {
        var selectLabel = document.createElement('label');
        selectLabel.htmlFor = 'sim-' + field[0];
        selectLabel.textContent = field[1];
        var select = document.createElement('select');
        select.className = 'simulator-select';
        select.id = 'sim-' + field[0];
        select.dataset.field = field[0];
        select.dataset.default = field[4];
        field[3].forEach(function (optionData) {
          var option = document.createElement('option');
          option.value = optionData[0]; option.textContent = optionData[1];
          select.appendChild(option);
        });
        select.value = field[4];
        wrapper.append(selectLabel, select);
      } else {
        var head = document.createElement('div');
        head.className = 'simulator-field-head';
        var inputLabel = document.createElement('label');
        inputLabel.htmlFor = 'sim-' + field[0];
        inputLabel.textContent = field[1];
        var value = document.createElement('span');
        value.className = 'simulator-value';
        value.dataset.valueFor = field[0];
        var input = document.createElement('input');
        input.className = 'simulator-range';
        input.type = 'range'; input.id = 'sim-' + field[0]; input.dataset.field = field[0];
        input.min = field[2]; input.max = field[3]; input.value = field[4]; input.step = field[5];
        input.dataset.default = field[4]; input.dataset.unit = field[6];
        var labels = document.createElement('div');
        labels.className = 'simulator-range-labels';
        labels.innerHTML = '<span>' + field[2] + ' ' + field[6] + '</span><span>' + field[3] + ' ' + field[6] + '</span>';
        head.append(inputLabel, value);
        wrapper.append(head, input, labels);
      }
      fieldsHost.appendChild(wrapper);
    });
  }
  function values() {
    var current = {};
    fieldsHost.querySelectorAll('[data-field]').forEach(function (field) {
      current[field.dataset.field] = field.tagName === 'SELECT' ? field.value : number(field.value);
    });
    return current;
  }

  function updateRange(input) {
    var progress = (number(input.value) - number(input.min)) / (number(input.max) - number(input.min)) * 100;
    input.style.setProperty('--range-progress', progress + '%');
    var value = fieldsHost.querySelector('[data-value-for="' + input.dataset.field + '"]');
    if (value) value.textContent = input.value.replace('.', ',') + ' ' + input.dataset.unit;
  }

  function renderResults(result) {
    statusHost.textContent = result.status;
    explanationHost.textContent = result.explanation;
    resultsHost.innerHTML = '';
    result.results.forEach(function (item) {
      var card = document.createElement('div');
      card.className = 'simulator-result';
      var name = document.createElement('span');
      var value = document.createElement('strong');
      name.textContent = item[0]; value.textContent = item[1];
      card.append(name, value); resultsHost.appendChild(card);
    });
  }
  function resizeCanvas() {
    var box = canvas.getBoundingClientRect();
    var ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(box.width * ratio);
    canvas.height = Math.round(box.height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { width: box.width, height: box.height };
  }

  function draw(progress) {
    var size = resizeCanvas();
    context.clearRect(0, 0, size.width, size.height);
    config.draw(context, size.width, size.height, values(), progress, palette());
  }

  function refresh(progress) {
    var current = values();
    renderResults(config.calculate(current));
    draw(progress === undefined ? .25 : progress);
  }

  function stopAnimation() {
    if (animationId) cancelAnimationFrame(animationId);
    animationId = null;
    actionLabel.textContent = 'Simular novamente';
  }

  function animate(timestamp) {
    if (!animationStart) animationStart = timestamp;
    var elapsed = timestamp - animationStart;
    var progress = (elapsed % 4000) / 4000;
    draw(progress);
    if (elapsed < 8000) animationId = requestAnimationFrame(animate);
    else stopAnimation();
  }
  createFields();
  formulaHost.textContent = config.formula;
  tipHost.textContent = config.tip;
  fieldsHost.querySelectorAll('input').forEach(updateRange);
  refresh(.15);

  fieldsHost.addEventListener('input', function (event) {
    if (event.target.matches('input')) updateRange(event.target);
    refresh(.15);
  });
  fieldsHost.addEventListener('change', function () { refresh(.15); });
  action.addEventListener('click', function () {
    if (animationId) cancelAnimationFrame(animationId);
    animationStart = 0;
    actionLabel.textContent = 'Simulando...';
    animationId = requestAnimationFrame(animate);
    renderResults(config.calculate(values()));
  });
  reset.addEventListener('click', function () {
    stopAnimation();
    fieldsHost.querySelectorAll('[data-field]').forEach(function (field) {
      field.value = field.dataset.default;
      if (field.tagName === 'INPUT') updateRange(field);
    });
    actionLabel.textContent = 'Simular';
    refresh(.15);
  });
  window.addEventListener('resize', function () { draw(.15); });

  var themeObserver = new MutationObserver(function () { draw(.15); });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
})();




