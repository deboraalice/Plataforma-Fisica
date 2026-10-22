from app import db

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)

    students = db.relationship('Student', backref='team', lazy='dynamic')