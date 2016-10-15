class RAMLSchemaError(Exception):
	pass

class DatabaseValidaitionError(RAMLSchemaError):
	def __init__(self, errors):
		self.errors = errors
		error_message = "Failed to validate document: {0}".format(errors)
		super().__init__(error_message)

class InvalidPageError(RAMLSchemaError):
	def __init__(self, page_num):
		self.page_num = page_num

class HTTPError(Exception):
    def to_dict(self):
        raise NotImplementedError

class BodyValidationHTTPError(HTTPError):
	def __init__(self, errors, status=422):
        self.errors = errors
        self.status = status
        self.error_type = error_type

    def to_dict(self):
		return {
            "error_type":"request_body_validation",
			"validation_errors":self.errors,
		}
class BodyDecodeHTTPError(HTTPError):
    def __init__(self, decode_error, status=400):
        self.decode_error = decode_error
        self.status = status
        self.error_type = error_type

    def to_dict(self):
        return {
            "error_type":"request_body_decode",
            "message":self.decode_error.msg,
            "position":self.decode_error.pos,
            "line_no":self.decode_error.line_no,
            "col_no":self.decode_error.col_no
        }

class InvalidPageHTTPError(HTTPError):
	def __init__(self, page_num, status=422):
        self.errors = errors
        self.page_num = page_num

    def to_dict(self):
		return {
            "error_type":"invalid_page_number",
			"page_number":self.page_num
		}
