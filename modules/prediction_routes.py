"""HTTP transport layer for burnsky prediction endpoints."""

from flask import Blueprint, jsonify, request


def create_prediction_blueprint(predict, limiter, cache):
    """Create prediction routes with explicit application dependencies."""
    prediction_bp = Blueprint('prediction', __name__)

    @prediction_bp.route('/predict', methods=['GET'])
    @limiter.limit('100 per hour')
    @cache.cached(timeout=300, query_string=True)
    def predict_burnsky():
        prediction_type = request.args.get('type', 'sunset')
        advance_hours = int(request.args.get('advance', 0))
        return jsonify(predict(prediction_type, advance_hours))

    @prediction_bp.route('/predict/sunrise', methods=['GET'])
    @limiter.limit('100 per hour')
    @cache.cached(timeout=300, query_string=True)
    def predict_sunrise():
        advance_hours = request.args.get('advance_hours', '0')
        return jsonify(predict('sunrise', advance_hours))

    @prediction_bp.route('/predict/sunset', methods=['GET'])
    @limiter.limit('100 per hour')
    @cache.cached(timeout=300, query_string=True)
    def predict_sunset():
        advance_hours = request.args.get('advance_hours', '0')
        return jsonify(predict('sunset', advance_hours))

    return prediction_bp