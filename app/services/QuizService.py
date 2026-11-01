from sqlalchemy.exc import IntegrityError

from app import db
from app.models.physics import (
    FirstQuestionScore,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizOption,
    QuizQuestion,
)
from app.models.point_transaction import PointTransaction
from app.services.PointsService import PointsService
from app.timeutils import agora_utc


class QuizError(ValueError):
    pass


class QuizService:
    @staticmethod
    def iniciar_tentativa(student_id, quiz_id):
        quiz = db.session.get(Quiz, quiz_id)
        if quiz is None or not quiz.is_active:
            raise QuizError("Este quiz não está disponível.")
        if not quiz.questions.first():
            raise QuizError("Este quiz ainda não tem questões.")

        tentativa = QuizAttempt(student_id=student_id, quiz_id=quiz.id)
        db.session.add(tentativa)
        db.session.commit()
        return tentativa

    @staticmethod
    def enviar_respostas(attempt_id, student_id, respostas):
        tentativa = db.session.get(QuizAttempt, attempt_id)
        if tentativa is None or tentativa.student_id != student_id:
            raise QuizError("Tentativa não encontrada.")
        if tentativa.completed_at is not None:
            raise QuizError("Esta tentativa já foi concluída.")
        if not isinstance(respostas, dict):
            raise QuizError("As respostas devem ser enviadas como um objeto por questão.")

        questoes = QuizQuestion.query.filter_by(quiz_id=tentativa.quiz_id).all()
        if not questoes:
            raise QuizError("Este quiz não tem questões.")
        questoes_por_id = {questao.id: questao for questao in questoes}

        respostas_normalizadas = {}
        for raw_question_id, raw_option_id in respostas.items():
            try:
                question_id = int(raw_question_id)
            except (TypeError, ValueError):
                raise QuizError("Uma das questões enviadas é inválida.")
            if question_id not in questoes_por_id or question_id in respostas_normalizadas:
                raise QuizError("Uma das questões não pertence a este quiz.")

            if raw_option_id in (None, ""):
                respostas_normalizadas[question_id] = None
                continue
            try:
                option_id = int(raw_option_id)
            except (TypeError, ValueError):
                raise QuizError("Uma das alternativas enviadas é inválida.")

            alternativa = db.session.get(QuizOption, option_id)
            if alternativa is None or alternativa.question_id != question_id:
                raise QuizError("Uma alternativa não pertence à questão correspondente.")
            respostas_normalizadas[question_id] = alternativa

        correct_count = 0
        points_awarded = 0
        first_answers_recorded = 0
        points_per_correct = max(0, tentativa.quiz.points_per_correct)

        for question_id, alternativa in respostas_normalizadas.items():
            # Questões em branco não contam como tentativa individual; o aluno
            # ainda poderá respondê-las em uma tentativa posterior.
            if alternativa is None:
                continue

            questao = questoes_por_id[question_id]
            correta = bool(alternativa.is_correct)
            correct_count += int(correta)
            db.session.add(
                QuizAnswer(
                    attempt_id=tentativa.id,
                    question_id=question_id,
                    selected_option_id=alternativa.id,
                    is_correct=correta,
                )
            )

            if FirstQuestionScore.query.filter_by(
                student_id=student_id,
                question_id=question_id,
            ).first():
                continue

            points_for_question = points_per_correct if correta else 0
            try:
                # A restrição única por aluno e questão protege a pontuação
                # mesmo se duas tentativas forem enviadas ao mesmo tempo.
                with db.session.begin_nested():
                    first_score = FirstQuestionScore(
                        student_id=student_id,
                        question_id=question_id,
                        attempt_id=tentativa.id,
                        points_awarded=points_for_question,
                    )
                    db.session.add(first_score)
                    db.session.flush()
                    if points_for_question:
                        PointsService.conceder(
                            student_id=student_id,
                            quantidade=points_for_question,
                            motivo=PointTransaction.QUIZ_FIRST,
                            ref_id=first_score.id,
                        )
                        db.session.flush()
                first_answers_recorded += 1
                points_awarded += points_for_question
            except IntegrityError:
                # Outra tentativa registrou primeiro a questão; não concede
                # pontos duplicados e mantém as respostas desta tentativa.
                continue

        tentativa.correct_count = correct_count
        tentativa.question_count = len(questoes)
        tentativa.completed_at = agora_utc()
        db.session.commit()

        return {
            "attempt_id": tentativa.id,
            "correct_count": correct_count,
            "question_count": len(questoes),
            "points_awarded": points_awarded,
            "first_answers_recorded": first_answers_recorded,
            "completed_at": tentativa.completed_at,
        }
