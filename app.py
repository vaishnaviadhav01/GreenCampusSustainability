from flask import Flask, render_template, redirect, url_for, request, abort,flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, ResourceUsage ,Quiz, QuizQuestion, QuizResult
from datetime import datetime
import io
import matplotlib.pyplot as plt
from flask import send_file
import csv
from werkzeug.utils import secure_filename






app = Flask(__name__)
app.config["SECRET_KEY"] = "green-campus-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///green_campus.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_only():
    if current_user.role != "admin":
        abort(403)

# Initialize database and default users
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password="admin123", role="admin")
        student = User(username="student", password="student123", role="student")
        db.session.add_all([admin, student])
        db.session.commit()

# ---------- AUTH ----------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            login_user(user)
            return redirect(url_for(
                "admin_dashboard" if user.role == "admin" else "student_dashboard"
            ))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already exists")

        new_user = User(username=username, password=password, role="student")
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

# ---------- ADMIN ----------
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    admin_only()
    return render_template("admin/dashboard.html")

@app.route("/admin/manage-users")
@login_required
def manage_users():
    admin_only()
    return render_template("admin/manage_users.html")





# ---------------- QUIZ MODULE (admin creating quiz)----------------

# Admin creates quiz
@app.route("/admin/create-quiz", methods=["GET", "POST"])
@login_required
def create_quiz():
    admin_only()
    if request.method == "POST":
        title = request.form["title"]
        questions = request.form.getlist("question")
        option_a = request.form.getlist("option_a")
        option_b = request.form.getlist("option_b")
        option_c = request.form.getlist("option_c")
        option_d = request.form.getlist("option_d")
        correct_answers = request.form.getlist("correct_answer")

        # Deactivate old quizzes
        Quiz.query.update({Quiz.is_active: False})
        db.session.commit()

        # Create new quiz
        quiz = Quiz(title=title, is_active=True)
        db.session.add(quiz)
        db.session.commit()

        for i in range(len(questions)):
            q = QuizQuestion(
                quiz_id=quiz.id,
                question=questions[i],
                option_a=option_a[i],
                option_b=option_b[i],
                option_c=option_c[i],
                option_d=option_d[i],
                correct_answer=correct_answers[i]
            )
            db.session.add(q)
        db.session.commit()
        flash("Quiz created successfully!", "success")
        return redirect(url_for("create_quiz"))
    return render_template("admin/create_quiz.html")



#----------------resourse_usage-------------------------


def parse_date(date_str):
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


@app.route("/admin/resource-usage", methods=["GET", "POST"])
@login_required
def resource_usage():
    admin_only()

    if request.method == "POST":

        # ---------- CSV UPLOAD ----------
        if "csv_file" in request.files:
            file = request.files["csv_file"]

            if file.filename.endswith(".csv"):
                stream = io.StringIO(file.stream.read().decode("UTF8"))
                csv_reader = csv.DictReader(stream)

                for row in csv_reader:
                    date = parse_date(row["date"])
                    if not date:
                        continue   # skip invalid rows safely


                    # Avoid duplicate dates
                    if not ResourceUsage.query.filter_by(date=date).first():
                        usage = ResourceUsage(
                            date=date,
                            electricity=float(row["electricity"]),
                            water=float(row["water"]),
                            waste=float(row["waste"])
                        )
                        db.session.add(usage)

                db.session.commit()
                flash("CSV file uploaded successfully!", "success")

            return redirect(url_for("resource_usage"))

        # ---------- DAILY MANUAL ENTRY ----------
        date = request.form["date"]
        electricity = request.form["electricity"]
        water = request.form["water"]
        waste = request.form["waste"]

        if not ResourceUsage.query.filter_by(
            date=datetime.strptime(date, "%Y-%m-%d").date()
        ).first():

            usage = ResourceUsage(
                date=datetime.strptime(date, "%Y-%m-%d").date(),
                electricity=float(electricity),
                water=float(water),
                waste=float(waste)
            )

            db.session.add(usage)
            db.session.commit()

        return redirect(url_for("resource_usage"))

    return render_template("admin/resource_usage.html")


@app.route("/admin/analytics")
@login_required
def analytics():
    admin_only()

    # Fetch all usage data
    usage_data = ResourceUsage.query.order_by(ResourceUsage.date).all()

    if not usage_data:
        months = []
        electricity = []
        water = []
        waste = []
        total_electricity = 0
        total_water = 0
        total_waste = 0
    else:
        months = [u.date.strftime("%b %Y") for u in usage_data]
        electricity = [u.electricity for u in usage_data]
        water = [u.water for u in usage_data]
        waste = [u.waste for u in usage_data]
        total_electricity = sum(electricity)
        total_water = sum(water)
        total_waste = sum(waste)

    monthly_avg = (
        (total_electricity + total_water + total_waste) / len(usage_data)
        if usage_data else 0
    )

    return render_template(
        "admin/analytics.html",
        months=months,
        electricity=electricity,
        water=water,
        waste=waste,
        total_electricity=total_electricity,
        total_water=total_water,
        total_waste=total_waste,
        monthly_avg=monthly_avg
    )

@app.route("/admin/results")
@login_required
def view_results():
    admin_only()
    return render_template("admin/view_results.html")



# Admin sees top 3 students
@app.route("/admin/top-students")
@login_required
def top_students():
    admin_only()
    top_results = (
        db.session.query(User.username, db.func.sum(QuizResult.score).label("total_score"))
        .join(QuizResult, User.id == QuizResult.user_id)
        .group_by(User.id)
        .order_by(db.desc("total_score"))
        .limit(3)
        .all()
    )
    return render_template("admin/top_students.html", top_results=top_results)


# ---------- STUDENT ----------
@app.route("/student/dashboard")
@login_required
def student_dashboard():
    return render_template("student/dashboard.html")



# Student attempts quiz
@app.route("/student/attempt-quiz", methods=["GET", "POST"])
@login_required
def student_attempt_quiz():
    # Only active quiz
    quiz = Quiz.query.filter_by(is_active=True).first()
    if not quiz:
        flash("No active quiz available.", "warning")
        return redirect(url_for("student_dashboard"))

    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).all()
    if request.method == "POST":
        score = 0
        for q in questions:
            selected = request.form.get(str(q.id))
            if selected == q.correct_answer:
                score += 1

        # Save result
        result = QuizResult(
            user_id=current_user.id,
            quiz_id=quiz.id,
            score=score,
            total=len(questions)
        )
        db.session.add(result)
        db.session.commit()
        flash(f"You scored {score} / {len(questions)}", "success")
        return redirect(url_for("view_score"))

    return render_template("student/attempt_quiz.html", quiz=quiz, questions=questions)






# Student views score
@app.route("/student/view-score")
@login_required
def view_score():
    results = QuizResult.query.filter_by(user_id=current_user.id).all()
    return render_template("student/view_score.html", results=results)





@app.route("/student/upload-contribution")
@login_required
def upload_contribution():
    return render_template("student/upload_contribution.html")

@app.route("/student/certificate")
@login_required
def certificate():
    return render_template("student/certificate.html",current_date=datetime.today().strftime("%d-%m-%Y"))

# ---------- CHARTS ----------
@app.route("/charts/<chart_name>")
@login_required
def charts(chart_name):
    admin_only()

    img = io.BytesIO()
    usage_data = ResourceUsage.query.order_by(ResourceUsage.date).all()
    if not usage_data:
        return "No data available", 404

    months = [u.date.strftime("%b %Y") for u in usage_data]
    electricity = [u.electricity for u in usage_data]
    water = [u.water for u in usage_data]
    waste = [u.waste for u in usage_data]

    if chart_name == "monthly":
        plt.figure(figsize=(6,4))
        plt.plot(months, electricity, marker='o', label='Electricity')
        plt.plot(months, water, marker='o', label='Water')
        plt.plot(months, waste, marker='o', label='Bio Waste')
        plt.title("Monthly Resource Usage")
        plt.ylabel("Units")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

    elif chart_name == "distribution":
        plt.figure(figsize=(4,4))
        plt.pie([sum(electricity), sum(water), sum(waste)],
                labels=["Electricity", "Water", "Bio Waste"],
                autopct='%1.1f%%',
                colors=['#4caf50','#2196f3','#ff9800'])
        plt.title("Resource Distribution")
        plt.tight_layout()

    elif chart_name == "electricity":
        plt.figure(figsize=(4,4))
        plt.bar(months, electricity, color='#4caf50')
        plt.title("Electricity Usage")
        plt.xticks(rotation=45)
        plt.tight_layout()

    elif chart_name == "water":
        plt.figure(figsize=(4,4))
        plt.bar(months, water, color='#2196f3')
        plt.title("Water Usage")
        plt.xticks(rotation=45)
        plt.tight_layout()

    elif chart_name == "waste":
        plt.figure(figsize=(4,4))
        plt.bar(months, waste, color='#ff9800')
        plt.title("Bio Waste")
        plt.xticks(rotation=45)
        plt.tight_layout()

    else:
        return "Chart not found", 404

    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return send_file(img, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)
