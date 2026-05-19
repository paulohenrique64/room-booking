from django.contrib import admin
from django.utils.html import format_html

from .models import Recurso, Sala


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao_curta', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']

    fieldsets = (
        ('Informações', {'fields': ('nome', 'descricao')}),
        ('Status', {'fields': ('ativo',)}),
        ('Auditoria', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def descricao_curta(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_curta.short_description = 'Descrição'


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'localizacao', 'capacidade_display', 'recursos_display', 'status_display', 'criado_em']
    list_filter = ['ativa', 'predio', 'capacidade', 'criado_em']
    search_fields = ['nome', 'predio', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']
    filter_horizontal = ['recursos']

    fieldsets = (
        ('Informações Básicas', {'fields': ('nome', 'predio', 'andar', 'capacidade')}),
        ('Recursos', {'fields': ('recursos',)}),
        ('Detalhes', {'fields': ('descricao', 'ativa')}),
        ('Auditoria', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def localizacao(self, obj):
        return f'{obj.predio} - Andar {obj.andar}'
    localizacao.short_description = 'Localização'

    def capacidade_display(self, obj):
        return f'{obj.capacidade} pessoas'
    capacidade_display.short_description = 'Capacidade'

    def recursos_display(self, obj):
        recursos = obj.recursos.all()
        if not recursos:
            return '—'
        return ', '.join([r.nome for r in recursos])
    recursos_display.short_description = 'Recursos'

    def status_display(self, obj):
        if obj.ativa:
            return format_html('<span style="color: green;">✓ Ativa</span>')
        return format_html('<span style="color: red;">✗ Inativa</span>')
    status_display.short_description = 'Status'
