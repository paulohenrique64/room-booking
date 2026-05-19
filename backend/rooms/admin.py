from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
from .models import Recurso, Sala, Reserva, CancelamentoReserva, HistoricoReserva


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao_curta', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']

    fieldsets = (
        ('Informações', {
            'fields': ('nome', 'descricao')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
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
        ('Informações Básicas', {
            'fields': ('nome', 'predio', 'andar', 'capacidade')
        }),
        ('Recursos', {
            'fields': ('recursos',)
        }),
        ('Detalhes', {
            'fields': ('descricao', 'ativa')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
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


class HistoricoReservaInline(admin.TabularInline):
    model = HistoricoReserva
    extra = 0
    readonly_fields = ['acao', 'usuario', 'data_hora', 'descricao']
    can_delete = False

    def has_add_permission(self, request):
        return False


class CancelamentoReservaInline(admin.StackedInline):
    model = CancelamentoReserva
    extra = 0
    readonly_fields = ['data_cancelamento']
    can_delete = False

    def has_add_permission(self, request):
        return False


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['id_display', 'sala', 'professor_nome', 'data_hora_display', 'duracao_display', 'status_display', 'criado_em']
    list_filter = ['status', 'data', 'sala__predio', 'criado_em']
    search_fields = ['sala__nome', 'professor__first_name', 'professor__last_name', 'motivo']
    readonly_fields = ['criado_em', 'atualizado_em']
    inlines = [HistoricoReservaInline, CancelamentoReservaInline]
    date_hierarchy = 'data'

    fieldsets = (
        ('Reserva', {
            'fields': ('sala', 'professor', 'data', 'hora_inicio', 'hora_fim')
        }),
        ('Detalhes', {
            'fields': ('motivo', 'status')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def id_display(self, obj):
        return f'#{obj.id}'
    id_display.short_description = 'ID'

    def professor_nome(self, obj):
        return f'{obj.professor.get_full_name() or obj.professor.username}'
    professor_nome.short_description = 'Professor'

    def data_hora_display(self, obj):
        return f'{obj.data} ({obj.hora_inicio} - {obj.hora_fim})'
    data_hora_display.short_description = 'Data/Horário'

    def duracao_display(self, obj):
        from datetime import datetime
        inicio = datetime.combine(obj.data, obj.hora_inicio)
        fim = datetime.combine(obj.data, obj.hora_fim)
        duracao_minutos = int((fim - inicio).total_seconds() / 60)
        horas = duracao_minutos // 60
        minutos = duracao_minutos % 60
        return f'{horas}h {minutos}min' if horas > 0 else f'{minutos}min'
    duracao_display.short_description = 'Duração'

    def status_display(self, obj):
        colors = {
            'ativa': 'green',
            'cancelada': 'red',
            'finalizada': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        status_label = dict(Reserva.STATUS_CHOICES).get(obj.status, obj.status)
        return format_html(f'<span style="color: {color}; font-weight: bold;">{status_label}</span>')
    status_display.short_description = 'Status'

    def get_queryset(self, request):
        # Permitir que administradores vejam todas as reservas
        return super().get_queryset(request)

    actions = ['cancelar_reservas_selecionadas']

    def cancelar_reservas_selecionadas(self, request, queryset):
        """Action para cancelar múltiplas reservas"""
        reservas_ativas = queryset.filter(status='ativa')
        canceladas = 0
        for reserva in reservas_ativas:
            reserva.status = 'cancelada'
            reserva.save()
            CancelamentoReserva.objects.create(
                reserva=reserva,
                motivo='Cancelada via admin',
                cancelado_por=request.user
            )
            canceladas += 1
        self.message_user(request, f'{canceladas} reserva(s) cancelada(s) com sucesso.')
    cancelar_reservas_selecionadas.short_description = 'Cancelar reservas selecionadas'


@admin.register(CancelamentoReserva)
class CancelamentoReservaAdmin(admin.ModelAdmin):
    list_display = ['reserva', 'professor_nome', 'cancelado_por_display', 'data_cancelamento']
    list_filter = ['data_cancelamento']
    search_fields = ['reserva__sala__nome', 'reserva__professor__first_name', 'reserva__professor__last_name']
    readonly_fields = ['reserva', 'cancelado_por', 'data_cancelamento']

    fieldsets = (
        ('Informações', {
            'fields': ('reserva', 'cancelado_por')
        }),
        ('Detalhes', {
            'fields': ('motivo',)
        }),
        ('Auditoria', {
            'fields': ('data_cancelamento',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def professor_nome(self, obj):
        return f'{obj.reserva.professor.get_full_name() or obj.reserva.professor.username}'
    professor_nome.short_description = 'Professor'

    def cancelado_por_display(self, obj):
        return f'{obj.cancelado_por.get_full_name() or obj.cancelado_por.username}' if obj.cancelado_por else 'Sistema'
    cancelado_por_display.short_description = 'Cancelado por'


@admin.register(HistoricoReserva)
class HistoricoReservaAdmin(admin.ModelAdmin):
    list_display = ['reserva', 'acao', 'usuario_display', 'data_hora']
    list_filter = ['acao', 'data_hora']
    search_fields = ['reserva__sala__nome', 'usuario__first_name', 'usuario__last_name', 'descricao']
    readonly_fields = ['reserva', 'acao', 'usuario', 'data_hora', 'descricao']
    date_hierarchy = 'data_hora'

    fieldsets = (
        ('Informações', {
            'fields': ('reserva', 'acao', 'usuario')
        }),
        ('Detalhes', {
            'fields': ('descricao', 'data_hora')
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def usuario_display(self, obj):
        return f'{obj.usuario.get_full_name() or obj.usuario.username}' if obj.usuario else 'Sistema'
    usuario_display.short_description = 'Usuário'

