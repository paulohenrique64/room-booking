class HtmxMixin:
    """
    Retorna partial quando a requisição é HTMX.
    Defina partial_template_name e template_name (página completa).
    """

    partial_template_name = None

    def get_template_names(self):
        if getattr(self.request, 'htmx', False) and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()
