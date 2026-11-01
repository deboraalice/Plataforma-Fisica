# FísicaFlow

Plataforma web que une **organização de estudos** (metas, tarefas, progresso) a **simuladores interativos** e conteúdo de Física, para que o estudante aprenda experimentando e não só memorizando fórmulas.

> **Status:** em desenvolvimento (Projeto Integrador).

## Sobre o projeto

Muitos estudantes do Ensino Médio têm dificuldade em ligar fórmulas e leis da Física a situações do dia a dia, e nem toda escola tem laboratório. Esta plataforma permite alterar variáveis (atrito, massa, força, velocidade) em simuladores no navegador e ver o efeito em tempo real, além de reunir conteúdo teórico, vídeos e ferramentas de planejamento em um só lugar.

A plataforma é **complementar** ao Google Sala de Aula: ela não gerencia turmas, entregas ou notas, e foca em conteúdo, simulação e acompanhamento do progresso.

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Back-end | Python, Flask, SQLAlchemy |
| Front-end | HTML5, CSS3, JavaScript, Canvas API |
| Banco de dados | *(a confirmar: SQLite, MySQL ou PostgreSQL)* |
| Autenticação | SUAP (planejado); e-mail e senha com hash |
| Versionamento e gestão | Git, GitHub e GitHub Projects (Kanban) |

## Como executar

```bash
# 1. Clonar o repositório
git clone https://github.com/<usuario>/Plataforma-Fisica.git
cd Plataforma-Fisica

# 2. Criar e ativar o ambiente virtual
python -m venv venv
source venv/bin/activate (CMD: .bat ou Powershell: .ps1)       # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instalar as dependências
pip install -r requirements.txt

# 5. Iniciar a aplicação
flask --app run run --debug
```

A aplicação ficará disponível em `http://localhost:5000`.

### Variáveis de ambiente

Exemplo de `.env` (não envie este arquivo ao GitHub):

```
SECRET_KEY=troque-por-uma-chave-segura
DATABASE_URL=sqlite:///app.db
# Credenciais do SUAP (quando a integração for feita)
SUAP_CLIENT_ID=
SUAP_CLIENT_SECRET=
```

## Estrutura do projeto

```
Plataforma-Fisica/
├── app/
│   ├── models/        # Modelos do SQLAlchemy
│   ├── services/      # Regras de negócio
│   ├── routes/        # Rotas e controladores
│   ├── templates/     # Páginas HTML
│   └── static/        # CSS, JavaScript e imagens (inclui os simuladores)
├── requirements.txt
├── .env.example
└── README.md
```

## Equipe

**Discentes**

- Débora Alice de Oliveira Santos
- Maria Helen Moreno de Araújo
- Joanny Câmara Maranhão

**Orientadores**

- Bruna Raissa Gomes dos Santos Batista
- Leo Moreira Silva
- Adorilson Bezerra
