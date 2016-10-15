from jsonschema import Draft4Validator

def get_json_errors(self, json_document, schema):
    validator = Draft4Validator(schema)
    validation_errors = []
    for error in validator.iter_errors(json_document):
            error_dict = {
                "message":error.message,
                "path":error.path
            }
        validation_errors.append(error_dict)
    return validation_errors
