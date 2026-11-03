"""Rotas dos simuladores interativos de Física."""

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from app.models.physics import PhysicsTopic


simulators = Blueprint("simulators", __name__)


SIMULATOR_INFO = {
    "cinematica": {
        "eyebrow": "Movimento no trânsito",
        "description": "Acelere um carro e observe como velocidade e distância mudam com o tempo.",
    },
    "dinamica": {
        "eyebrow": "Carrinho de supermercado",
        "description": "Compare força aplicada, atrito e massa para descobrir o movimento do carrinho.",
    },
    "energia-trabalho": {
        "eyebrow": "Montanha-russa",
        "description": "Transforme energia potencial em cinética durante a descida de um carrinho.",
    },
    "termodinamica": {
        "eyebrow": "Água no fogão",
        "description": "Descubra a energia e o tempo necessários para aquecer água em casa.",
    },
    "ondas-som": {
        "eyebrow": "Som de uma caixa acústica",
        "description": "Altere frequência e amplitude e acompanhe a forma da onda sonora.",
    },
    "optica": {
        "eyebrow": "Lente de uma câmera",
        "description": "Mude a posição do objeto e veja onde e como a lente forma a imagem.",
    },
    "eletricidade": {
        "eyebrow": "Lâmpada doméstica",
        "description": "Monte um circuito simples e relacione tensão, resistência, corrente e potência.",
    },
    "magnetismo": {
        "eyebrow": "Eletroímã caseiro",
        "description": "Controle corrente e número de espiras para alterar a intensidade do eletroímã.",
    },
    "hidrostatica": {
        "eyebrow": "Objeto dentro da piscina",
        "description": "Teste pressão e empuxo para prever se um objeto afunda ou flutua.",
    },
    "gravitacao": {
        "eyebrow": "Peso em outros mundos",
        "description": "Compare seu peso e uma órbita circular na Terra, Lua, Marte e Júpiter.",
    },
}


@simulators.route("/fisica/simuladores/<slug>")
@login_required
def physics_simulator(slug):
    info = SIMULATOR_INFO.get(slug)
    topic = PhysicsTopic.query.filter_by(slug=slug).first()
    if info is None or topic is None:
        flash("Simulador não encontrado.", "warning")
        return redirect(url_for("fisica"))
    return render_template("physics/simulator.html", topico=topic, simulator=info)
