from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class Professor(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=True)

    matricula_suap = db.Column(db.String(32), index=True, unique=True, nullable=True)

    teams = db.relationship('Team', backref='professor', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"professor:{self.id}"

    def _repr_(self):
        return f"<Professor {self.email}>"