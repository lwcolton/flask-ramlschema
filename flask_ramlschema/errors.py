

class RAMLSchemaError:
	pass

class DatabaseValidaitionError(RAMLSchemaError):
	def __init__(self, errors):
		self.errors = errors
		error_message = "Failed to validate document: {0}".format(errors)
		super().__init__(error_message)
