from . import db

class Voter(db.Model):
    tsc_number = db.Column(db.String(20), primary_key=True)
    voted = db.Column(db.Boolean, default=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    position = db.Column(db.String(50))  # Chairman, Secretary, Treasurer
    photo = db.Column(db.String(100))
    manifesto = db.Column(db.Text)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tsc_number = db.Column(db.String(20), db.ForeignKey('voter.tsc_number'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    position = db.Column(db.String(50))
