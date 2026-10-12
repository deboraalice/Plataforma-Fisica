from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    email = db.Column(db.String(128), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    matricula_suap = db.Column(db.String(32), index=True, unique=True, nullable=True)

    is_if = db.Column(db.Boolean, default=False, nullable=False)

    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"student:{self.id}"

    def __repr__(self):
        return f"<Student {self.email}>"
