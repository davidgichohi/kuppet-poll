from app import create_app, db
from app.models import Voter
import csv

app = create_app()
app.app_context().push()

db.create_all()

# Load TSC numbers from CSV
with open('data/tsc.csv', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        tsc_number = row[0]
        if not Voter.query.get(tsc_number):
            voter = Voter(tsc_number=tsc_number)
            db.session.add(voter)

db.session.commit()
print("Database initialized with TSC numbers.")
