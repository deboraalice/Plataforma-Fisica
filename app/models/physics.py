from app import db
from app.timeutils import agora_utc
from sqlalchemy import CheckConstraint


class PhysicsUnit(db.Model):
    __tablename__ = "physics_unit"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    slug = db.Column(db.String(128), nullable=False, unique=True)
    position = db.Column(db.Integer, nullable=False, default=0)

    topics = db.relationship(
        "PhysicsTopic",
        backref="unit",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="PhysicsTopic.position",
    )


class PhysicsTopic(db.Model):
    __tablename__ = "physics_topic"

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("physics_unit.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), nullable=False, unique=True)
    emoji = db.Column(db.String(16), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    solved_example = db.Column(db.Text, nullable=True)
    simulator_url = db.Column(db.String(255), nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)

    formulas = db.relationship(
        "PhysicsFormula",
        backref="topic",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="PhysicsFormula.position",
    )

    resources = db.relationship(
        "PhysicsResource",
        backref="topic",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    quizzes = db.relationship(
        "Quiz",
        backref="topic",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class Quiz(db.Model):
    __tablename__ = "quiz"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("physics_topic.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    points_per_correct = db.Column(db.Integer, nullable=False, default=1)

    questions = db.relationship(
        "QuizQuestion",
        backref="quiz",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.position",
    )


class PhysicsFormula(db.Model):
    __tablename__ = "physics_formula"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("physics_topic.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    expression = db.Column(db.String(255), nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)


class TopicCompletion(db.Model):
    __tablename__ = "topic_completion"
    __table_args__ = (
        db.UniqueConstraint("student_id", "topic_id", name="uq_topic_completion_student_topic"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("physics_topic.id"), nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=False, default=agora_utc)

    student = db.relationship("Student")
    topic = db.relationship("PhysicsTopic")


class PhysicsResource(db.Model):
    """Recurso geral da plataforma ou material suplementar de uma turma."""

    __tablename__ = "physics_resource"
    __table_args__ = (
        CheckConstraint(
            "(team_id IS NULL AND professor_id IS NULL) OR "
            "(team_id IS NOT NULL AND professor_id IS NOT NULL)",
            name="ck_physics_resource_scope",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("physics_topic.id"), nullable=False, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=True, index=True)
    professor_id = db.Column(db.Integer, db.ForeignKey("professor.id"), nullable=True, index=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(1024), nullable=False)
    youtube_video_id = db.Column(db.String(11), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=agora_utc)
    updated_at = db.Column(db.DateTime, nullable=False, default=agora_utc, onupdate=agora_utc)

    team = db.relationship("Team", backref=db.backref("physics_resources", lazy="dynamic"))
    professor = db.relationship("Professor", backref=db.backref("physics_resources", lazy="dynamic"))

    @property
    def youtube_embed_url(self):
        if not self.youtube_video_id:
            return None
        return f"https://www.youtube.com/embed/{self.youtube_video_id}"


class QuizQuestion(db.Model):
    __tablename__ = "quiz_question"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False, index=True)
    prompt = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)

    options = db.relationship(
        "QuizOption",
        backref="question",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="QuizOption.position",
    )


class QuizOption(db.Model):
    __tablename__ = "quiz_option"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_question.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    position = db.Column(db.Integer, nullable=False, default=0)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempt"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    started_at = db.Column(db.DateTime, nullable=False, default=agora_utc)
    completed_at = db.Column(db.DateTime, nullable=True)
    correct_count = db.Column(db.Integer, nullable=False, default=0)
    question_count = db.Column(db.Integer, nullable=False, default=0)

    quiz = db.relationship("Quiz", backref=db.backref("attempts", lazy="dynamic"))
    student = db.relationship("Student", backref=db.backref("quiz_attempts", lazy="dynamic"))
    answers = db.relationship(
        "QuizAnswer",
        backref="attempt",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class QuizAnswer(db.Model):
    __tablename__ = "quiz_answer"
    __table_args__ = (
        db.UniqueConstraint("attempt_id", "question_id", name="uq_quiz_answer_attempt_question"),
    )

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempt.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_question.id"), nullable=False, index=True)
    selected_option_id = db.Column(db.Integer, db.ForeignKey("quiz_option.id"), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    answered_at = db.Column(db.DateTime, nullable=False, default=agora_utc)

    question = db.relationship("QuizQuestion")
    selected_option = db.relationship("QuizOption")


class FirstQuestionScore(db.Model):
    """Primeira resposta do aluno a uma questão, usada para pontuar uma vez."""

    __tablename__ = "first_question_score"
    __table_args__ = (
        db.UniqueConstraint("student_id", "question_id", name="uq_first_question_student_question"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_question.id"), nullable=False, index=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempt.id"), nullable=False)
    points_awarded = db.Column(db.Integer, nullable=False, default=0)
    recorded_at = db.Column(db.DateTime, nullable=False, default=agora_utc)

    student = db.relationship("Student")
    question = db.relationship("QuizQuestion")
    attempt = db.relationship("QuizAttempt")
