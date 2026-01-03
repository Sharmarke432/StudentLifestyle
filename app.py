from flask import Flask, redirect,render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta, time, datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student_balance.db' #using sqlite database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False #stop alchemy from tracking modifications, boost performance
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    study_blocks = db.relationship('StudyBlock', backref='user', lazy=True)

class StudyBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    subject = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  # e.g. "Monday"
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    location = db.Column(db.String(100))
    notes = db.Column(db.Text)

@app.route("/timetable", methods=["GET", "POST"])
def timetable():
    week_offset = int(request.args.get("week", 0))
    today = date.today()
    start_of_week = today + timedelta(weeks=week_offset, days=-today.weekday())

    if request.method == "POST":
        subject = request.form.get("subject")
        day = int(request.form.get("day_offset"))  # 0-6

        start_time_str = request.form.get("start_time")  # e.g. "19:00"
        end_time_str = request.form.get("end_time")      # e.g. "21:44"

        # 1) Parse strings into Python time objects
        start_hour, start_minute = map(int, start_time_str.split(":"))
        end_hour, end_minute = map(int, end_time_str.split(":"))

        start_time_obj = time(start_hour, start_minute)
        end_time_obj = time(end_hour, end_minute)

        block_date = start_of_week + timedelta(days=day)

        new_block = StudyBlock(
            user_id=1,  # temporary until auth
            subject=subject,
            day_of_week=block_date.strftime("%A"),
            start_time=start_time_obj,  # <- NOT the string
            end_time=end_time_obj,      # <- NOT the string
        )
        db.session.add(new_block)
        db.session.commit()

        return redirect(url_for("timetable", week=week_offset))


    #Fetch blocks for the current week (simplest: by day_of_week name)
    days = [(start_of_week + timedelta(days=i)) for i in range(7)]
    blocks_by_day = {d.strftime("%A"): [] for d in days}

    blocks = StudyBlock.query.filter_by(user_id=1).all()
    for b in blocks:
        if b.day_of_week in blocks_by_day:
            blocks_by_day[b.day_of_week].append(b)

    return render_template(
        "timetable.html",
        days=days,
        blocks_by_day=blocks_by_day,
        week_offset=week_offset,
    )

@app.post("/timetable/<int:block_id>/delete")
def delete_block(block_id):
    block = StudyBlock.query.get_or_404(block_id)
    # later: also check block.user_id == current_user.id
    db.session.delete(block)
    db.session.commit()
    week_offset = int(request.args.get("week", 0))
    return redirect(url_for("timetable", week=week_offset))


@app.route("/")
def home():
    return redirect(url_for("timetable"))

if __name__ == "__main__":
    app.run(debug=True)
