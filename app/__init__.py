from flask import Flask
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import py_eureka_client.eureka_client as eureka_client
import h2o

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Register the Flask application with Eureka
    eureka_client.init(
        eureka_server="http://localhost:9102/",
        app_name="python-predict-service",
        instance_port=5000,
        instance_ip="127.0.0.1"
    )

    # Initialize the H2O cluster
    h2o.init()

    # Swagger configuration
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger_predict.json'
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Workspaces_H2O_Flask-REST-Api"
        }
    )
    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

    with app.app_context():
        from app.controllers.prediction_controller import prediction_blueprint
        app.register_blueprint(prediction_blueprint)

    return app
