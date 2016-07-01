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