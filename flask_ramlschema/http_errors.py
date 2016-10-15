class HTTPError(Exception):
    pass

class BodyValidationError(HTTPError):
	def __init__(self, errors, status=422,
                 error_type="request_body_validation"):
        self.errors = errors
        self.status = status
        self.error_type = error_type

    def to_dict(self):
		return {
            "error_type":self.error_type,
			"validation_errors":self.errors
		}


class BodyDecodeError(HTTPError):
    def __init__(self, decode_error, status=400,
                 error_type="request_body_decode"):
        self.decode_error = decode_error
        self.status = status
        self.error_type = error_type

    def to_dict(self):
        return {
            "error_type":self.error_type,
            "message":self.decode_error.msg,
            "position":self.decode_error.pos,
            "line_no":self.decode_error.line_no,
            "col_no":self.decode_error.col_no
        }
