from flask import Blueprint, jsonify

# Blueprint for API routes
bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint.
    WHY: Establish baseline API for monitoring availability.
    WHAT: closes initial setup ticket.
    HOW: Extend by adding authentication; roll back by removing blueprint registration.
    """
    return jsonify({'status': 'ok'})

