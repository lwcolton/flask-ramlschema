import json

from flask import Response

class ValidationError(Exception):
    def __init__(self, errors, status_code=422, 
                 description="Validation Error"):
        self.errors = errors
        self.status_code = status_code
        self.description = description

    def to_dict(self):
        error_dict = {
            "errors":self.errors,
            "status_code":self.status_code,
            "description":self.description
        }
        return error_dict

def handle_validation_error(error):
    error_json = json.dumps(error.to_dict())
    response = Response(response=error_json, status=422)
    return response

def register_error_handlers(flask_app):
	flask_app.register_error_handler(ValidationError, handle_validation_error)

