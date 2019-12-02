import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [questions.format() for questions in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    # CORS(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,POST,PATCH,PUT,DELETE,OPTIONS')

        return response

    @app.route('/questions')
    def get_questions():
        questions = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, questions)
        categories = Category.query.order_by(Category.id).all()

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': [
                category.format() for category in categories
            ],
        }), 200

    @app.route('/categories')
    def get_categories():
        selection = Category.query.all()
        categories = [category.format() for category in selection]
        return jsonify({
            'success': True,
            'categories': categories,
            'total_categories': len(Category.query.all())
        }), 200

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        if new_question is None \
            or new_answer is None \
                or new_category is None \
                or new_difficulty is None:
            abort(400)
        try:
            question = Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty
            )
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id,
                'message': 'Question created'
            }), 201

        except Exception as e:
            abort(422)

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            }), 200
        except Exception as e:
            if question is None:
                abort(404)
            else:
                abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        search_query = request.get_json().get('searchTerm', None)
        selection = Question.query.filter(
            Question.question.ilike('%{}%'.format(search_query))).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
        }), 200

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_categories(category_id):
        selection = Question.query.filter_by(category=category_id).all()
        questions = [question.format() for question in selection]

        return jsonify({
            'success': True,
            'questions': questions,
            'totalQuestions': len(questions),
            'currentCategory': category_id
        }), 200

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        try:

            data = request.get_json()
            previous_questions = data.get('previous_questions')
            category = data.get('quiz_category')

            if category['id'] == 0:
                questions = Question.query.all()

            else:
                questions = Question.query.filter_by(
                    category=category['id']).all()

            random_index = random.randint(0, len(questions)-1)
            next_question = questions[random_index]

            selected = False
            count = 0

            while selected is False:
                if next_question.id in previous_questions:
                    random_index = random.randint(0, len(questions)-1)
                    next_question = questions[random_index]
                else:
                    selected = True
                if count == len(questions):
                    break
                count += 1

            next_question = next_question.format()
            return jsonify({
                'success': True,
                'question': next_question,
            }), 200
        except Exception as e:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable Entity"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        }), 400
    return app
