from rest_framework.views import exception_handler


class DomainError(Exception):
    """
    Exceção para erros de lógica de negócio / domain.
    
    Usada para validações que violam regras de negócio,
    não apenas validações de dados.
    """
    pass


def custom_exception_handler(exc, context):
    """Handler centralizado para padronizar respostas de erro da API."""
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, dict) and 'detail' in response.data:
            response.data = {
                'erro': str(response.data['detail']),
                'codigo': response.status_code,
            }
        elif isinstance(response.data, dict):
            response.data = {
                'erro': response.data,
                'codigo': response.status_code,
            }

    return response
