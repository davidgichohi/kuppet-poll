from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import db, Voter, Candidate, Vote

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def voter_login():
    if request.method == 'POST':
        tsc_number = request.form['tsc_number'].strip()
        voter = Voter.query.get(tsc_number)
        if not voter:
            flash('Invalid TSC Number.', 'danger')
            return redirect(url_for('main.voter_login'))
        if voter.voted:
            flash('You have already voted.', 'warning')
            return redirect(url_for('main.voter_login'))
        return redirect(url_for('main.vote_page', tsc_number=tsc_number))
    return render_template('voter_login.html')


@main.route('/vote/<tsc_number>', methods=['GET', 'POST'])
def vote_page(tsc_number):
    voter = Voter.query.get(tsc_number)
    if not voter or voter.voted:
        flash("Unauthorized or already voted.", "danger")
        return redirect(url_for('main.voter_login'))

    if request.method == 'POST':
        for position in ['Chairman', 'Secretary General', 'Treasurer']:
            candidate_id = request.form.get(position)
            if candidate_id:
                vote = Vote(tsc_number=tsc_number, candidate_id=int(candidate_id), position=position)
                db.session.add(vote)
        voter.voted = True
        db.session.commit()
        flash("Thank you for voting!", "success")
        return redirect(url_for('main.voter_login'))

    positions = ['Chairman', 'Secretary General', 'Treasurer']
    candidates_by_position = {
        position: Candidate.query.filter_by(position=position).all() for position in positions
    }

    return render_template('vote_page.html', tsc_number=tsc_number, candidates=candidates_by_position)


import os
from flask import current_app
from werkzeug.utils import secure_filename

@main.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == current_app.config['ADMIN_USERNAME'] and password == current_app.config['ADMIN_PASSWORD']:
            return redirect(url_for('main.admin_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')


@main.route('/admin/dashboard')
def admin_dashboard():
    positions = ['Chairman', 'Secretary General', 'Treasurer']
    results = {}
    for position in positions:
        votes = db.session.query(Candidate.name, db.func.count(Vote.id))\
            .join(Vote, Candidate.id == Vote.candidate_id)\
            .filter(Candidate.position == position)\
            .group_by(Candidate.name).all()
        results[position] = votes
    return render_template('admin_dashboard.html')


@main.route('/admin/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        manifesto = request.form['manifesto']
        photo_file = request.files['photo']
        photo_filename = secure_filename(photo_file.filename)
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
        photo_file.save(photo_path)

        candidate = Candidate(name=name, position=position, manifesto=manifesto, photo=photo_filename)
        db.session.add(candidate)
        db.session.commit()

        flash('Candidate added successfully!', 'success')
        return redirect(url_for('main.add_candidate'))

    return render_template('add_candidate.html')
@main.route('/admin/view_votes')
def view_votes():
    positions = ['Chairman', 'Secretary General', 'Treasurer']
    results = {}
    for position in positions:
        votes = db.session.query(Candidate.name, Candidate.photo, db.func.count(Vote.id))\
            .join(Vote, Candidate.id == Vote.candidate_id)\
            .filter(Candidate.position == position)\
            .group_by(Candidate.name, Candidate.photo).all()
        results[position] = votes
    return render_template('view_votes.html', results=results)
@main.route('/admin/add_voters', methods=['GET', 'POST'])
def add_voters():
    if request.method == 'POST':
        if 'tsc_number' in request.form:
            # Single entry
            tsc_number = request.form['tsc_number'].strip()

            if not tsc_number.isdigit():
                flash('TSC number must be numeric.', 'danger')
            elif Voter.query.get(tsc_number):
                flash('TSC number already exists.', 'warning')
            else:
                db.session.add(Voter(tsc_number=tsc_number))
                db.session.commit()
                flash('TSC member added successfully.', 'success')

        elif 'csv_file' in request.files:
            # Bulk upload
            file = request.files['csv_file']
            if not file.filename.endswith('.csv'):
                flash('Please upload a valid CSV file.', 'danger')
                return redirect(url_for('main.add_voters'))

            stream = file.stream.read().decode('utf-8').splitlines()
            added = 0
            skipped = 0
            for line in stream:
                tsc = line.strip()
                if tsc.isdigit():
                    existing = Voter.query.get(tsc)
                    if existing:
                        if existing.voted:
                            skipped += 1
                        else:
                            skipped += 1  # Already in system
                    else:
                        db.session.add(Voter(tsc_number=tsc))
                        added += 1
                else:
                    skipped += 1  # Not numeric
            db.session.commit()
            flash(f'{added} TSC numbers added. {skipped} skipped (invalid, duplicates, or voted).', 'info')

        return redirect(url_for('main.add_voters'))

    return render_template('add_voters.html')
@main.route('/admin/view_voters')
def view_voters():
    voters = Voter.query.order_by(Voter.tsc_number).all()
    return render_template('view_voters.html', voters=voters)
@main.route('/admin/clear_votes', methods=['GET', 'POST'])
def clear_votes():
    if request.method == 'POST':
        entered_password = request.form.get('password')
        admin_password = current_app.config['ADMIN_PASSWORD']

        if entered_password == admin_password:
            Vote.query.delete()
            for voter in Voter.query.all():
                voter.voted = False
            db.session.commit()
            flash('All votes cleared and voter statuses reset.', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Incorrect password. Votes not cleared.', 'danger')
            return redirect(url_for('main.clear_votes'))

    return render_template('clear_votes.html')
@main.route('/admin/view_candidates')
def view_candidates():
    candidates = Candidate.query.order_by(Candidate.position).all()
    return render_template('view_candidates.html', candidates=candidates)
@main.route('/admin/edit_candidate/<int:candidate_id>', methods=['GET', 'POST'])
def edit_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)

    if request.method == 'POST':
        candidate.name = request.form['name']
        candidate.position = request.form['position']
        candidate.manifesto = request.form['manifesto']

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename != '':
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                candidate.photo = filename

        db.session.commit()
        flash('Candidate details updated.', 'success')
        return redirect(url_for('main.view_candidates'))

    return render_template('edit_candidate.html', candidate=candidate)
@main.route('/admin/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)

    # Optional: Check if candidate has votes
    vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()
    if vote_count > 0:
        flash('Cannot delete candidate with existing votes.', 'danger')
        return redirect(url_for('main.view_candidates'))

    db.session.delete(candidate)
    db.session.commit()
    flash('Candidate deleted successfully.', 'success')
    return redirect(url_for('main.view_candidates'))


