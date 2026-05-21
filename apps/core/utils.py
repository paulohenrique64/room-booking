"""
Utility functions compartilhadas.
"""
from datetime import datetime
from django.core.exceptions import ValidationError


def parse_data(data_input):
    """
    Converte string de data para date object.
    
    Args:
        data_input: str no formato YYYY-MM-DD ou date object
    
    Returns:
        datetime.date
        
    Raises:
        ValidationError: Se formato inválido
        
    Example:
        >>> parse_data('2024-05-21')
        datetime.date(2024, 5, 21)
        
        >>> parse_data(datetime.date(2024, 5, 21))
        datetime.date(2024, 5, 21)
    """
    if isinstance(data_input, datetime.date):
        return data_input
    
    if not isinstance(data_input, str):
        raise ValidationError(f"Data deve ser string ou date, recebido {type(data_input).__name__}")
    
    try:
        return datetime.strptime(data_input, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError("Data deve estar no formato YYYY-MM-DD (ex: 2024-05-21)")
