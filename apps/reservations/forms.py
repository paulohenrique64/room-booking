from django import forms

from apps.rooms.models import Sala

from .constants import ReservaStatus
from .models import Reserva


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['sala', 'data', 'hora_inicio', 'hora_fim', 'motivo']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
            'sala': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sala'].queryset = Sala.objects.filter(ativa=True).order_by('predio', 'nome')


class ReservaCancelarForm(forms.Form):
    motivo = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Motivo do cancelamento'}),
    )


class ReservaFiltroForm(forms.Form):
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(ReservaStatus.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    data = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
