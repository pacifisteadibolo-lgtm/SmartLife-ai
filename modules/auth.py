from flask import Blueprint
auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

@auth_bp.route('/login')
def login():
    return 'login — à implémenter S1'

@auth_bp.route('/register')
def register():
    return 'register — à implémenter S1'
