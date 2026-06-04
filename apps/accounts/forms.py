from django import forms
from django.contrib.auth.models import Group, Permission, User


FIELD_CLASS = 'w-full bg-white border border-outline-variant rounded-xl px-4 py-2.5 text-xs text-on-surface focus:outline-none focus:border-primary-base focus:ring-1 focus:ring-primary-base'


ACTION_LABELS = {
    'add': 'Criar',
    'change': 'Editar',
    'delete': 'Excluir',
    'view': 'Visualizar',
}

MODEL_LABELS = {
    'cancelamentoreserva': 'Cancelamentos de reserva',
    'group': 'Grupos de acesso',
    'historicreserva': 'Históricos de reserva',
    'historicoreserva': 'Históricos de reserva',
    'notificationdismissal': 'Notificações dispensadas',
    'permission': 'Permissões',
    'recurso': 'Equipamentos',
    'reserva': 'Reservas',
    'sala': 'Salas',
    'user': 'Usuários',
}


def permission_label(permission):
    action, _, model = permission.codename.partition('_')
    action_label = ACTION_LABELS.get(action, permission.name)
    model_label = MODEL_LABELS.get(model, permission.content_type.model.replace('_', ' '))
    return f'{action_label} {model_label}'


class UserAdminForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': FIELD_CLASS, 'autocomplete': 'new-password'}),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Grupos',
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'first_name': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'last_name': forms.TextInput(attrs={'class': FIELD_CLASS}),
            'email': forms.EmailInput(attrs={'class': FIELD_CLASS}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-outline-variant text-primary-base focus:ring-primary-base'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'rounded border-outline-variant text-primary-base focus:ring-primary-base'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'rounded border-outline-variant text-primary-base focus:ring-primary-base'}),
        }
        labels = {
            'username': 'Nome de usuário',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
            'is_active': 'Conta ativa',
            'is_staff': 'Áreas administrativas',
            'is_superuser': 'Acesso total ao sistema',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].help_text = 'Obrigatória ao criar. Deixe em branco para manter a senha atual.'
        if self.is_bound:
            self.selected_group_ids = [int(pk) for pk in self.data.getlist('groups') if str(pk).strip()]
        elif self.instance and self.instance.pk:
            self.selected_group_ids = list(self.instance.groups.values_list('pk', flat=True))
        else:
            self.selected_group_ids = []

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.pk and not password:
            raise forms.ValidationError('Informe uma senha para criar o usuário.')
        return password

    def save(self, commit=True):
        password = self.cleaned_data.pop('password', None)
        user = super().save(commit=False)
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user


class GroupAdminForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Permissões',
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={'class': FIELD_CLASS}),
        }
        labels = {
            'name': 'Nome do grupo',
            'permissions': 'Permissões',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_apps = {'accounts', 'auth', 'core', 'reservations', 'rooms'}
        self.fields['permissions'].queryset = self.fields['permissions'].queryset.filter(
            content_type__app_label__in=allowed_apps
        )
        if self.is_bound:
            self.selected_permission_ids = [int(pk) for pk in self.data.getlist('permissions') if str(pk).strip()]
        elif self.instance and self.instance.pk:
            self.selected_permission_ids = list(self.instance.permissions.values_list('pk', flat=True))
        else:
            self.selected_permission_ids = []
        self.permission_options = [
            {
                'id': permission.pk,
                'label': permission_label(permission),
                'code': f'{permission.content_type.app_label}.{permission.codename}',
            }
            for permission in self.fields['permissions'].queryset
        ]
