class DomainError(Exception):
    """Erro de regra de negócio do domínio de reservas."""

    def __init__(self, message, code=None):
        self.message = message
        self.code = code or 'domain_error'
        super().__init__(message)
