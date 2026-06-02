from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from apps.reservations import selectors as reservation_selectors
from apps.reservations.constants import ReservaStatus
from apps.reservations.models import Reserva
from apps.rooms.models import Recurso, Sala
from apps.rooms.forms import RecursoForm, SalaForm
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render, redirect


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.localdate()
        salas = list(Sala.objects.filter(ativa=True).order_by('predio', 'andar', 'nome'))
        reservas_qs = (
            reservation_selectors.reservas_para_usuario(self.request.user)
            .filter(data=hoje, status=ReservaStatus.ATIVA)
            .select_related('sala')
            .order_by('hora_inicio')
        )

        reservas_por_sala = {}
        for reserva in reservas_qs:
            reservas_por_sala.setdefault(reserva.sala_id, []).append(reserva)

        rooms_data = []
        for sala in salas:
            bookings = []
            for reserva in reservas_por_sala.get(sala.id, []):
                left, width = self._get_time_offsets(reserva.hora_inicio, reserva.hora_fim)
                bookings.append(
                    {
                        'id': reserva.id,
                        'title': reserva.titulo,
                        'start_time': reserva.hora_inicio.strftime('%H:%M'),
                        'end_time': reserva.hora_fim.strftime('%H:%M'),
                        'left': left,
                        'width': width,
                    }
                )

            rooms_data.append(
                {
                    'id': sala.id,
                    'name': sala.nome,
                    'capacity': sala.capacidade,
                    'image': self._extract_image_url(sala.descricao),
                    'bookings': bookings,
                }
            )

        total_rooms = len(salas)
        occupied_count = len(reservas_por_sala)
        available_count = max(total_rooms - occupied_count, 0)
        capacity_pct = round((occupied_count / total_rooms) * 100) if total_rooms else 0

        now_time = timezone.localtime().time()

        now_booking = None
        next_booking = None

        for reserva in reservas_qs:
            if reserva.hora_inicio <= now_time <= reserva.hora_fim:
                now_booking = reserva
                break

        if not now_booking:
            next_booking = reservas_qs.filter(hora_inicio__gt=now_time).first()

        spotlight_booking = now_booking or next_booking
        is_occupied_now = now_booking is not None

        upcoming_room = (
            spotlight_booking.sala if spotlight_booking else (salas[0] if salas else None)
        )

        context.update(
            {
                'today': hoje,
                'total_rooms': total_rooms,
                'occupied_count': occupied_count,
                'available_count': available_count,
                'capacity_pct': capacity_pct,
                'floors_count': len({sala.andar for sala in salas}),
                'upcoming_booking': spotlight_booking,
                'upcoming_room': upcoming_room,
                'upcoming_room_image': self._extract_image_url(upcoming_room.descricao) if upcoming_room else '',
                'is_occupied_now': is_occupied_now,
                'rooms': rooms_data,
                'current_time_label': timezone.localtime().strftime('%H:%M'),
                'current_time_left': self._get_now_offset(),
            }
        )
        return context

    def _extract_image_url(self, descricao):
        if not descricao:
            return ''
        marker = 'Imagem:'
        if marker not in descricao:
            return ''
        remainder = descricao.split(marker, 1)[1].strip()
        url = remainder.split('|', 1)[0].strip()
        return url

    def _get_time_offsets(self, start_time, end_time):
        def parse_time(value):
            if isinstance(value, str):
                return datetime.strptime(value, '%H:%M').time()
            return value

        start = parse_time(start_time)
        end = parse_time(end_time)
        start_hour = start.hour + start.minute / 60
        end_hour = end.hour + end.minute / 60
        timeline_start = 9.0
        total_hours = 6.0
        timeline_end = timeline_start + total_hours

        clamped_start = max(timeline_start, min(timeline_end, start_hour))
        clamped_end = max(timeline_start, min(timeline_end, end_hour))
        if clamped_end < clamped_start:
            clamped_end = clamped_start

        left = ((clamped_start - timeline_start) / total_hours) * 100
        width = ((clamped_end - clamped_start) / total_hours) * 100
        return left, width

    def _get_now_offset(self):
        now = timezone.localtime().time()
        now_hour = now.hour + now.minute / 60 + now.second / 3600
        timeline_start = 9.0
        total_hours = 6.0
        timeline_end = timeline_start + total_hours

        clamped_now = max(timeline_start, min(timeline_end, now_hour))
        return ((clamped_now - timeline_start) / total_hours) * 100


class EquipmentListView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/equipment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['equipamentos'] = (
            Recurso.objects.all()
            .prefetch_related('salas')
            .order_by('nome')
        )
        return context


def equipamento_modal(request, pk=None):
    """Return modal form for create/edit via HTMX or full page fallback."""
    instance = None
    view_context = request.GET.get('context') or request.POST.get('context')
    if pk:
        instance = get_object_or_404(Recurso, pk=pk)

    if request.method == 'POST':
        form = RecursoForm(request.POST, instance=instance)
        form_is_valid = form.is_valid()
        if form_is_valid:
            form.save()
            if getattr(request, 'htmx', False):
                equipamentos = Recurso.objects.all().prefetch_related('salas').order_by('nome')
                if view_context == 'rooms':
                    response = render(request, 'rooms/partials/_equipment_sidebar.html', {'equipamentos': equipamentos})
                else:
                    response = render(request, 'pages/partials/_equipment_list.html', {'equipamentos': equipamentos})
                response['HX-Trigger'] = 'modalClosed'
                return response
            return redirect('equipment')
    else:
        form = RecursoForm(instance=instance)

    template_name = 'pages/partials/_form_equipamento.html'
    response = render(request, template_name, {'form': form, 'pk': pk, 'context': view_context})
    if getattr(request, 'htmx', False) and request.method == 'POST' and not form_is_valid:
        response['HX-Retarget'] = '#modal-container'
    return response


def equipamento_delete(request, pk):
    recurso = get_object_or_404(Recurso, pk=pk)
    if request.method in ('POST', 'DELETE'):
        recurso.delete()
        if getattr(request, 'htmx', False):
            return HttpResponse(status=204)
        return redirect('equipment')
    return HttpResponse(status=405)


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.localdate()
        
        # Get all active reservations for today
        reservas_hoje = (
            Reserva.objects.filter(data=hoje, status=ReservaStatus.ATIVA)
            .select_related('sala')
            .order_by('hora_inicio')
        )
        
        # Get all rooms
        salas = Sala.objects.filter(ativa=True).order_by('nome')
        
        # Calculate metrics
        total_bookings = reservas_hoje.count()
        peak_hour = self._calculate_peak_hour(reservas_hoje)
        
        # Calculate gauge stroke-dashoffset (SVG circle circumference = 2*pi*r = ~251.2 for r=40)
        max_bookings = 20  # assume max 20 bookings for gauge scaling
        gauge_ratio = min(total_bookings / max_bookings, 1.0)  # cap at 100%
        stroke_dashoffset = 251.2 * (1 - gauge_ratio)  # offset when bookings increase
        
        # Calculate room utilization
        room_utilization = []
        for sala in salas[:3]:  # Show top 3 rooms
            reservas_sala = reservas_hoje.filter(sala=sala)
            if reservas_sala.exists():
                total_hours = 0
                for r in reservas_sala:
                    start = r.hora_inicio
                    end = r.hora_fim
                    total_hours += (end.hour + end.minute/60) - (start.hour + start.minute/60)
                utilization_pct = round((total_hours / 8) * 100)  # assume 8-hour workday
                room_utilization.append({
                    'name': sala.nome,
                    'utilization': min(100, utilization_pct)
                })
        
        context.update({
            'total_bookings': total_bookings,
            'peak_hour': peak_hour,
            'utilization_ratio': f'{round((total_bookings / len(salas)) * 100) if salas else 0}%' if total_bookings else '0%',
            'stroke_dashoffset': stroke_dashoffset,
            'room_utilization': room_utilization,
            'hoje': hoje,
        })
        return context
    
    def _calculate_peak_hour(self, reservas):
        """Calculate the peak booking hour."""
        if not reservas:
            return '09:00 - 11:00'
        
        hours = {}
        for r in reservas:
            hour = r.hora_inicio.hour
            hours[hour] = hours.get(hour, 0) + 1
        
        if not hours:
            return '09:00 - 11:00'
        
        peak = max(hours, key=hours.get)
        start = f'{peak:02d}:00'
        end = f'{peak+1:02d}:00'
        return f'{start} - {end}'


def sala_modal(request, pk=None):
    instance = None
    if pk:
        instance = get_object_or_404(Sala, pk=pk)

    if request.method == 'POST':
        form = SalaForm(request.POST, instance=instance)
        form_is_valid = form.is_valid()
        if form_is_valid:
            form.save()
            if getattr(request, 'htmx', False):
                salas = Sala.objects.all().prefetch_related('recursos').order_by('predio', 'andar', 'nome')
                equipamentos = Recurso.objects.all().order_by('nome')
                response = render(request, 'rooms/partials/_lista_salas.html', {'salas': salas, 'equipamentos': equipamentos})
                response['HX-Trigger'] = 'modalClosed'
                return response
            return redirect('rooms:lista')
    else:
        form = SalaForm(instance=instance)

    response = render(request, 'rooms/partials/_form_sala.html', {'form': form, 'pk': pk})
    if getattr(request, 'htmx', False) and request.method == 'POST' and not form_is_valid:
        response['HX-Retarget'] = '#modal-container'
    return response


def sala_delete(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    if request.method in ('POST', 'DELETE'):
        sala.delete()
        if getattr(request, 'htmx', False):
            salas = Sala.objects.all().prefetch_related('recursos').order_by('predio', 'andar', 'nome')
            equipamentos = Recurso.objects.all().order_by('nome')
            response = render(request, 'rooms/partials/_lista_salas.html', {'salas': salas, 'equipamentos': equipamentos})
            response['HX-Trigger'] = 'modalClosed'
            return response
        return redirect('rooms:lista')
    return HttpResponse(status=405)
