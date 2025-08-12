from flask import Flask, jsonify
from routes import configure_routes
import os

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///./database.db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    os.environ['UPLOAD_FOLDER'] = 'uploads'

    configure_routes(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)