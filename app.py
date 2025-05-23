from flask import Flask
from api.routes import api_bp
import os

def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
