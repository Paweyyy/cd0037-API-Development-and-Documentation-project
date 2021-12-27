import json
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    CORS(app, ressources={ r"*/api/*": { "origins": '*' }})

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    def paginate_questions(request, selection):
        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]

        return current_questions

    def format_categories(cat):
        res = {}
        for c in cat:
            res[int(c["id"])] = c["type"]
        return res

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        categories_formatted = format_categories([category.format() for category in categories])
        if len(categories) == 0:
            abort(404)

        return(
            jsonify({
                "success": True,
                "categories": categories_formatted
            })
        )

    @app.route('/questions', methods=["GET"])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.order_by(Category.id).all()
        categories_formatted = format_categories([category.format() for category in categories])

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(Question.query.all()),
                "categories": categories_formatted,
                "current_category": None
            }
        )


    @app.route('/questions/<int:question_id>', methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.filter_by(id=question_id).one_or_none()
            if question == None:
                abort(404)

            print(question)
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                }
            )
        except Exception as e:
            print(e)
            abort(404)

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_questions_form_category(category_id):
        selection = Question.query.order_by(Question.id).all()
        c = Category.query.filter_by(id=category_id).one_or_none()

        if c is None:
            abort(404)

        category = c.format()["type"]
        selection = Question.query.filter_by(category=category_id).all()
        current_questions = paginate_questions(request, selection)

        return(jsonify({
            "success": True,
            "questions": current_questions,
            "total_questions": len(Question.query.filter_by(id=category_id).all()),
            "current_category": category
        }))

    
    @app.route('/questions', methods=["POST"])
    def create_question():
        body = request.get_json()
        search_term = body.get("searchTerm", None)
        try:
            if search_term:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike("%{}%".format(search_term))
                )
                # selection = Book.query.order_by(Book.id).filter(or_(Book.title.ilike('%{}%'.format(search)), Book.author.ilike('%{}%'.format(search))))
                current_questions = paginate_questions(request, selection)
                print(current_questions)
                return jsonify(
                    {
                        "success": True,
                        "questions": current_questions,
                        "totalQuestions": len(Question.query.all()),
                        "currentCategory": "History"
                    }
                )
            else:
                new_question = body.get("question", None)
                new_answer = body.get("answer", None)
                new_difficulty = body.get("difficulty", None)
                new_category = body.get("category", None)

                if new_question == None or new_answer == None or new_difficulty == None or new_category == None:
                    abort(422)
                
                question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
                question.insert()

                return jsonify(
                    {
                        "success": True,
                    }
                )

        except Exception as e:
            print(e)
            abort(422)

    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():
        body = request.get_json()
        previous_questions = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)
        print(previous_questions, quiz_category)

        if previous_questions is None or quiz_category is None:
            abort(404)
        
        if int(quiz_category["id"]) != 0:
            questions = Question.query.filter_by(category=int(quiz_category["id"])).all()
        else:
            questions = Question.query.all()

        if len(questions) == 0:
            abort(422)
            
        q_f = [qu.format() for qu in questions]
        filtered = list(filter(lambda q: q["id"] not in previous_questions, q_f))
        res = random.choice(filtered)

        return jsonify({
            "success": True,
            "question": res
        })


    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(500)
    def bad_request(error):
        return jsonify({"success": False, "error": 500, "message": "internal server error"}), 500

    return app

