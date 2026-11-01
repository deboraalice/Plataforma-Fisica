from sqlalchemy.exc import IntegrityError

from app import db
from app.models.physics import PhysicsFormula, PhysicsTopic, PhysicsUnit, TopicCompletion


TOPICOS_INICIAIS = [
    {
        "unit": "Mecânica", "unit_slug": "mecanica", "unit_position": 1,
        "title": "Cinemática", "slug": "cinematica", "emoji": "🚗", "position": 1,
        "summary": "Movimento, velocidade, aceleração e trajetória.",
        "content": "A Cinemática estuda o movimento dos corpos sem se preocupar com suas causas. Ela descreve trajetórias, velocidades e acelerações através de equações matemáticas.",
        "example": "Um carro parte do repouso (v₀ = 0) com aceleração a = 2 m/s². Qual a velocidade após 5 segundos?\n\nv = v₀ + a·t\nv = 0 + 2 × 5 = 10 m/s\n\nO carro atingiu 10 m/s (≈ 36 km/h) após 5 segundos.",
        "formulas": [
            ("Velocidade média", "v = Δs / Δt", "Razão entre o deslocamento e o intervalo de tempo."),
            ("MUV – Velocidade", "v = v₀ + a·t", "No movimento uniformemente variado, a velocidade muda de forma constante."),
            ("MUV – Posição", "s = s₀ + v₀·t + ½·a·t²", "Equação horária da posição no movimento uniformemente variado."),
            ("Equação de Torricelli", "v² = v₀² + 2·a·Δs", "Relaciona velocidades, aceleração e deslocamento sem usar o tempo."),
        ],
    },
    {
        "unit": "Mecânica", "unit_slug": "mecanica", "unit_position": 1,
        "title": "Dinâmica", "slug": "dinamica", "emoji": "⚡", "position": 2,
        "summary": "Forças, Leis de Newton e atrito.",
        "content": "A Dinâmica estuda as causas dos movimentos. As Leis de Newton relacionam força resultante, massa e aceleração e ajudam a descrever interações como peso, normal e atrito.",
        "example": "Um carrinho de 2 kg sofre uma força resultante de 6 N. Qual é sua aceleração?\n\nΣF = m·a\na = ΣF / m = 6 / 2 = 3 m/s²\n\nA aceleração do carrinho é 3 m/s².",
        "formulas": [
            ("Segunda Lei de Newton", "ΣF = m·a", "A força resultante sobre um corpo é o produto da massa pela aceleração."),
            ("Força peso", "P = m·g", "Força gravitacional exercida sobre um corpo próximo à superfície de um astro."),
            ("Atrito cinético", "Fₐₜ = μ·N", "Modelo do módulo do atrito cinético; μ é o coeficiente de atrito."),
        ],
    },
    {
        "unit": "Mecânica", "unit_slug": "mecanica", "unit_position": 1,
        "title": "Energia e Trabalho", "slug": "energia-trabalho", "emoji": "🔋", "position": 3,
        "summary": "Energia cinética, potencial e conservação.",
        "content": "Trabalho mede a transferência de energia realizada por uma força ao longo de um deslocamento. A energia mecânica pode aparecer como energia cinética, ligada ao movimento, ou potencial, ligada à posição.",
        "example": "Um objeto de 2 kg move-se a 3 m/s. Qual é sua energia cinética?\n\nEₖ = ½·m·v²\nEₖ = ½ × 2 × 3² = 9 J\n\nA energia cinética é 9 joules.",
        "formulas": [
            ("Trabalho de força constante", "W = F·d·cos(θ)", "Válida para força constante; θ é o ângulo entre força e deslocamento."),
            ("Energia cinética", "Eₖ = ½·m·v²", "Energia associada ao movimento de um corpo."),
            ("Energia potencial gravitacional", "Eₚ = m·g·h", "Energia associada à altura em relação a um nível de referência."),
        ],
    },
    {
        "unit": "Termologia", "unit_slug": "termologia", "unit_position": 2,
        "title": "Termodinâmica", "slug": "termodinamica", "emoji": "🌡️", "position": 4,
        "summary": "Calor, temperatura e leis dos gases.",
        "content": "A Termodinâmica investiga trocas de energia na forma de calor e trabalho e suas relações com temperatura, pressão e volume. Calor é energia em trânsito devido a uma diferença de temperatura.",
        "example": "Quanto calor é necessário para aquecer 0,5 kg de água em 10 °C? Use c = 4.200 J/(kg·°C).\n\nQ = m·c·ΔT\nQ = 0,5 × 4.200 × 10 = 21.000 J\n\nSão necessários 21.000 J, sem considerar mudanças de fase.",
        "formulas": [
            ("Calor sensível", "Q = m·c·ΔT", "Relaciona calor, massa, calor específico e variação de temperatura."),
            ("Gás ideal", "p·V = n·R·T", "Equação de estado para um gás ideal, com temperatura em kelvin."),
        ],
    },
    {
        "unit": "Ondulatória", "unit_slug": "ondulatoria", "unit_position": 3,
        "title": "Ondas e Som", "slug": "ondas-som", "emoji": "〰️", "position": 5,
        "summary": "Tipos de ondas, frequência e amplitude.",
        "content": "Ondas transportam energia sem transportar matéria de forma permanente. O som é uma onda mecânica: precisa de um meio material para se propagar.",
        "example": "Uma onda tem frequência de 2 Hz e comprimento de onda de 3 m. Qual é sua velocidade?\n\nv = λ·f\nv = 3 × 2 = 6 m/s\n\nA onda se propaga a 6 m/s.",
        "formulas": [
            ("Velocidade de propagação", "v = λ·f", "Relaciona velocidade, comprimento de onda e frequência."),
            ("Período e frequência", "T = 1 / f", "O período é o tempo de uma oscilação completa."),
        ],
    },
    {
        "unit": "Óptica", "unit_slug": "optica", "unit_position": 4,
        "title": "Óptica", "slug": "optica", "emoji": "🔦", "position": 6,
        "summary": "Luz, reflexão, refração e lentes.",
        "content": "A Óptica estuda a luz e sua interação com materiais. Reflexão, refração e formação de imagens explicam fenômenos vistos em espelhos, lentes e instrumentos ópticos.",
        "example": "Um objeto está a 30 cm de um espelho côncavo com distância focal de 10 cm. Onde se forma a imagem?\n\n1/f = 1/p + 1/p′\n1/10 = 1/30 + 1/p′\n1/p′ = 1/15, portanto p′ = 15 cm.\n\nA imagem se forma a 15 cm do espelho.",
        "formulas": [
            ("Equação dos espelhos esféricos", "1/f = 1/p + 1/p′", "Relaciona distância focal, posição do objeto e posição da imagem."),
            ("Índice de refração", "n = c / v", "Razão entre a velocidade da luz no vácuo e no meio."),
        ],
    },
    {
        "unit": "Eletromagnetismo", "unit_slug": "eletromagnetismo", "unit_position": 5,
        "title": "Eletricidade", "slug": "eletricidade", "emoji": "🔌", "position": 7,
        "summary": "Corrente, tensão, resistência e circuitos.",
        "content": "A Eletricidade descreve cargas elétricas e seu movimento em circuitos. Tensão, corrente e resistência se relacionam pela Lei de Ohm em componentes ôhmicos.",
        "example": "Um resistor de 4 Ω está ligado a uma tensão de 12 V. Qual corrente o atravessa?\n\nU = R·i\ni = U/R = 12/4 = 3 A\n\nA corrente elétrica é 3 A.",
        "formulas": [
            ("Lei de Ohm", "U = R·i", "Relaciona tensão, resistência e corrente em um resistor ôhmico."),
            ("Potência elétrica", "P = U·i", "Potência transferida em um componente elétrico."),
        ],
    },
    {
        "unit": "Eletromagnetismo", "unit_slug": "eletromagnetismo", "unit_position": 5,
        "title": "Magnetismo", "slug": "magnetismo", "emoji": "🧲", "position": 8,
        "summary": "Campos magnéticos e indução eletromagnética.",
        "content": "O Magnetismo estuda campos magnéticos e suas interações com ímãs, correntes elétricas e cargas em movimento. A variação do fluxo magnético pode induzir uma força eletromotriz.",
        "example": "Uma carga de 2 C move-se a 3 m/s perpendicularmente a um campo de 0,5 T. Qual força magnética atua nela?\n\nF = q·v·B·sen(θ)\nF = 2 × 3 × 0,5 × 1 = 3 N\n\nO módulo da força magnética é 3 N.",
        "formulas": [
            ("Força magnética sobre carga", "F = q·v·B·sen(θ)", "θ é o ângulo entre a velocidade e o campo magnético."),
            ("Fluxo magnético", "Φ = B·A·cos(θ)", "Para campo uniforme em uma superfície plana."),
        ],
    },
    {
        "unit": "Mecânica", "unit_slug": "mecanica", "unit_position": 1,
        "title": "Hidrostática", "slug": "hidrostatica", "emoji": "💧", "position": 9,
        "summary": "Pressão, empuxo e fluidos em equilíbrio.",
        "content": "A Hidrostática estuda fluidos em repouso. A pressão em um líquido aumenta com a profundidade e o empuxo é a força resultante exercida pelo fluido sobre um corpo imerso.",
        "example": "Qual é a pressão manométrica a 2 m de profundidade na água? Use ρ = 1.000 kg/m³ e g = 9,8 m/s².\n\np = ρ·g·h\np = 1.000 × 9,8 × 2 = 19.600 Pa\n\nA pressão manométrica é 19.600 Pa.",
        "formulas": [
            ("Pressão em fluido", "p = ρ·g·h", "Pressão manométrica a uma profundidade h em um fluido de densidade ρ."),
            ("Empuxo", "E = ρ·g·V", "Força de empuxo para o volume V de fluido deslocado."),
        ],
    },
    {
        "unit": "Mecânica", "unit_slug": "mecanica", "unit_position": 1,
        "title": "Gravitação", "slug": "gravitacao", "emoji": "🪐", "position": 10,
        "summary": "Gravidade, órbitas e interação entre massas.",
        "content": "A Gravitação descreve a atração entre corpos com massa. A lei da gravitação universal relaciona a força à massa dos corpos e à distância entre seus centros.",
        "example": "Qual é o peso aproximado de uma pessoa de 2 kg na Terra? Use g = 9,8 m/s².\n\nP = m·g\nP = 2 × 9,8 = 19,6 N\n\nO peso é aproximadamente 19,6 N.",
        "formulas": [
            ("Gravitação universal", "F = G·m₁·m₂ / r²", "Força de atração entre duas massas separadas pela distância r."),
            ("Campo gravitacional", "g = G·M / r²", "Aceleração gravitacional a uma distância r do centro de uma massa M."),
        ],
    },
]


class PhysicsService:
    @staticmethod
    def seed_conteudo_inicial():
        for dados in TOPICOS_INICIAIS:
            unidade = PhysicsUnit.query.filter_by(slug=dados["unit_slug"]).first()
            if unidade is None:
                unidade = PhysicsUnit(
                    name=dados["unit"],
                    slug=dados["unit_slug"],
                    position=dados["unit_position"],
                )
                db.session.add(unidade)
                db.session.flush()

            topico = PhysicsTopic.query.filter_by(slug=dados["slug"]).first()
            if topico is None:
                topico = PhysicsTopic(
                    unit_id=unidade.id,
                    title=dados["title"],
                    slug=dados["slug"],
                    emoji=dados["emoji"],
                    summary=dados["summary"],
                    content=dados["content"],
                    solved_example=dados["example"],
                    position=dados["position"],
                )
                db.session.add(topico)
                db.session.flush()
            else:
                topico.emoji = topico.emoji or dados["emoji"]
                topico.summary = topico.summary or dados["summary"]
                topico.content = topico.content or dados["content"]
                topico.solved_example = topico.solved_example or dados["example"]
                topico.position = dados["position"]

            nomes_existentes = {f.name for f in topico.formulas.all()}
            for posicao, (nome, expression, explanation) in enumerate(dados["formulas"], start=1):
                if nome not in nomes_existentes:
                    db.session.add(
                        PhysicsFormula(
                            topic_id=topico.id,
                            name=nome,
                            expression=expression,
                            explanation=explanation,
                            position=posicao,
                        )
                    )
        db.session.commit()

    @staticmethod
    def listar_topicos(student_id=None):
        topicos = (
            PhysicsTopic.query.join(PhysicsUnit)
            .order_by(PhysicsTopic.position, PhysicsTopic.id)
            .all()
        )
        concluidos = set()
        if student_id is not None:
            concluidos = {
                row[0]
                for row in db.session.query(TopicCompletion.topic_id)
                .filter_by(student_id=student_id)
                .all()
            }
        return [
            {
                "topico": topico,
                "concluido": topico.id in concluidos,
                "progresso": 100 if topico.id in concluidos else 0,
            }
            for topico in topicos
        ]

    @staticmethod
    def buscar_topico(slug, student_id=None):
        topico = PhysicsTopic.query.filter_by(slug=slug).first()
        if topico is None:
            return None, False
        concluido = False
        if student_id is not None:
            concluido = TopicCompletion.query.filter_by(
                student_id=student_id,
                topic_id=topico.id,
            ).first() is not None
        return topico, concluido

    @staticmethod
    def concluir_topico(student_id, topic_id):
        if TopicCompletion.query.filter_by(student_id=student_id, topic_id=topic_id).first():
            return False
        db.session.add(TopicCompletion(student_id=student_id, topic_id=topic_id))
        try:
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False

    @staticmethod
    def resumo(student_id):
        total = PhysicsTopic.query.count()
        concluidos = TopicCompletion.query.filter_by(student_id=student_id).count()
        return {
            "concluidos": concluidos,
            "total": total,
            "resumo": f"{concluidos} de {total} tópicos concluídos",
        }
