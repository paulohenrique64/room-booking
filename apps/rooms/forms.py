from django import forms
from django.core.exceptions import ValidationError

from .models import Recurso, Sala



def _extract_image_url(descricao):
    if not descricao:
        return ''
    marker = 'Imagem:'
    if marker not in descricao:
        return ''
    remainder = descricao.split(marker, 1)[1].strip()
    return remainder.split('|', 1)[0].strip()


def _strip_image_text(descricao):
    if not descricao:
        return ''
    marker = 'Imagem:'
    if marker not in descricao:
        return descricao
    remainder = descricao.split(marker, 1)[1]
    parts = remainder.split('|', 1)
    if len(parts) == 2:
        return parts[1].strip()
    return ''


class RecursoForm(forms.ModelForm):
    ICON_CHOICES = [
        ('videocam', 'Projetor / Vídeo'),
        ('tv', 'Painel Smart TV / LCD'),
        ('edit_note', 'Quadro / Notas'),
        ('local_cafe', 'Café / Alimentação'),
        ('home_repair_service', 'Serviços'),
        ('headphones', 'Áudio / Fones'),
        ('devices', 'Dispositivos'),
        ('computer', 'Computador'),
        ('phone_in_talk', 'Telefone'),
        ('videogame_asset', 'Equipamento Técnico'),
    ]
    
    icone = forms.ChoiceField(
        choices=ICON_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'w-full bg-white border border-outline-variant rounded-xl px-3 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base cursor-pointer appearance-none'}),
    )
    
    class Meta:
        model = Recurso
        fields = ['nome', 'descricao', 'quantidade', 'icone']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
            'quantidade': forms.NumberInput(attrs={'min': 0, 'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
        }


class SalaForm(forms.ModelForm):
    imagem_url = forms.URLField(
        required=False,
        label='URL da Imagem da Sala (Placeholder)',
    )
    recursos = forms.ModelMultipleChoiceField(
        queryset=Recurso.objects.all().order_by('nome'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Comodidades Pré-instaladas',
    )

    class Meta:
        model = Sala
        fields = ['nome', 'predio', 'andar', 'capacidade', 'descricao', 'imagem_url', 'recursos', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
            'predio': forms.TextInput(attrs={'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
            'andar': forms.NumberInput(attrs={'min': 0, 'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
            'capacidade': forms.NumberInput(attrs={'min': 1, 'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
            'imagem_url': forms.URLInput(attrs={'class': 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'rounded border-outline-variant text-primary-base focus:ring-primary-base'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        imagem_url = (self.cleaned_data.get('imagem_url') or '').strip()
        descricao_texto = (self.cleaned_data.get('descricao') or '').strip()
        descricao_parts = []
        if imagem_url:
            descricao_parts.append(f'Imagem: {imagem_url}')
        if descricao_texto:
            descricao_parts.append(descricao_texto)
        instance.descricao = ' | '.join(descricao_parts)

        # Get old recursos before saving (to compare changes)
        old_recursos = set()
        if instance.pk:
            old_recursos = set(instance.recursos.values_list('pk', flat=True))
        
        if commit:
            instance.save()
            self.save_m2m()
            
            # Decrement quantity for newly added resources
            new_recursos = set(r.pk for r in self.cleaned_data.get('recursos', []))
            added_recursos = new_recursos - old_recursos
            for recurso_id in added_recursos:
                recurso = Recurso.objects.get(pk=recurso_id)
                if recurso.quantidade > 0:
                    recurso.quantidade -= 1
                    recurso.save()
        
        return instance

    def clean_recursos(self):
        recursos = self.cleaned_data.get('recursos') or []
        indisponiveis = [recurso.nome for recurso in recursos if recurso.quantidade <= 0]
        if indisponiveis:
            nomes = ', '.join(indisponiveis)
            raise ValidationError(f'O(s) equipamento(s) {nomes} estão sem estoque.')
        return recursos

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if self.is_bound:
            self.selected_recursos_ids = [int(pk) for pk in self.data.getlist('recursos') if str(pk).strip()]
        elif instance and instance.pk:
            self.initial.setdefault('imagem_url', _extract_image_url(instance.descricao))
            self.initial.setdefault('descricao', _strip_image_text(instance.descricao))
            self.selected_recursos_ids = list(instance.recursos.values_list('pk', flat=True))
        else:
            self.selected_recursos_ids = []


