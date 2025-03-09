
class UserAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)

with app.app_context():
    db.create_all()


@app.route('/admin_dashboard/analyze_questions')
@login_required
def analyze_questions():

    question_stats = (
        db.session.query(
            Question.id,
            Question.question_with_choices,
            db.func.count(UserAnswer.id).label("total_attempts"),
            db.func.sum(db.case([(UserAnswer.is_correct == True, 1)], else_=0)).label("correct_answers")
        )
        .outerjoin(UserAnswer, Question.id == UserAnswer.question_id)
        .group_by(Question.id)
        .all()
    )
    
 
    analysis_results = []
    for q in question_stats:
        success_rate = (q.correct_answers / q.total_attempts * 100) if q.total_attempts > 0 else 0
        analysis_results.append({
            "question": q.question_with_choices,
            "success_rate": success_rate,
            "total_attempts": q.total_attempts
        })
    
   
    hardest_questions = sorted(analysis_results, key=lambda x: x["success_rate"])[:5]

  
    wrong_answers = (
        db.session.query(UserAnswer.user_answer, db.func.count(UserAnswer.id).label("count"))
        .filter(UserAnswer.is_correct == False)
        .group_by(UserAnswer.user_answer)
        .order_by(db.desc("count"))
        .limit(5)
        .all()
    )

    return render_template(
        "analyze_questions.html", 
        hardest_questions=hardest_questions, 
        wrong_answers=wrong_answers,
        title="Analyze Questions"
    )
