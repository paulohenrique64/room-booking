from django import forms
from django.utils import timezone

from apps.rooms.models import Sala

from .constants import ReservaStatus
from .models import Reserva


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['sala', 'data', 'hora_inicio', 'hora_fim', 'titulo', 'status']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'input-field'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'input-field'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'input-field'}),
            'titulo': forms.TextInput(attrs={'class': 'input-field'}),
            'sala': forms.Select(attrs={'class': 'select-field appearance-none pr-10'}),
            'status': forms.Select(attrs={'class': 'select-field'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sala'].queryset = Sala.objects.filter(ativa=True).order_by('predio', 'nome')
        if not self.instance or not self.instance.pk:
            self.fields.pop('status', None)
            if not self.is_bound:
                now = timezone.localtime()
                self.fields['data'].initial = timezone.localdate()
                self.fields['hora_inicio'].initial = now.strftime('%H:%M')


class ReservaCancelarForm(forms.Form):
    motivo = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Motivo do cancelamento'}),
    )


class ReservaFiltroForm(forms.Form):
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(ReservaStatus.choices),
        widget=forms.Select(
            attrs={
                'class': 'select-field appearance-none pr-10'
            }
        )
    )
    data = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'input-field'}),
    )
