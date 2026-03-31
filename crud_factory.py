from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError
from models import db


def create_crud_blueprint(model, url_prefix: str):
    bp = Blueprint(
        f'{model.__tablename__.lower()}_api',
        __name__,
        url_prefix=url_prefix
    )

    fillable = getattr(model, '__fillable__', set())
    readonly = getattr(model, '__readonly__', set())
    pk = model.primary_key()

    # -------------------------------------------------
    # GET ALL / POST
    # -------------------------------------------------
    @bp.route('/', methods=['GET', 'POST'])
    @login_required
    def list_create():
        if request.method == 'GET':
            items = model.query.all()
            return jsonify([i.to_dict() for i in items])

        data = request.json or {}
        filtered = {k: v for k, v in data.items() if k in fillable}

        try:
            instance = model(**filtered)
            db.session.add(instance)
            db.session.commit()
            return jsonify({
                'message': 'created',
                'id': getattr(instance, pk)
            }), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

    # -------------------------------------------------
    # GET / PUT / DELETE
    # -------------------------------------------------
    @bp.route('/<id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def detail(id):
        instance = model.query.get_or_404(id)

        if request.method == 'GET':
            return jsonify(instance.to_dict())

        if request.method == 'PUT':
            data = request.json or {}
            for key, value in data.items():
                if key in fillable and key not in readonly:
                    setattr(instance, key, value)

            try:
                db.session.commit()
                return jsonify({'message': 'updated'})
            except SQLAlchemyError as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 400

        if request.method == 'DELETE':
            try:
                db.session.delete(instance)
                db.session.commit()
                return jsonify({'message': 'deleted'})
            except SQLAlchemyError as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 400

    return bp
