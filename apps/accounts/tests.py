from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse


class AccessManagementTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='admin', password='senha123', is_staff=True)
        self.user = User.objects.create_user(username='professor', password='senha123')

    def test_area_de_acessos_exige_staff(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:access'))

        self.assertNotEqual(response.status_code, 200)

    def test_staff_visualiza_area_de_acessos(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('accounts:access'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuários e Grupos')

    def test_cria_grupo_com_permissao(self):
        permission = Permission.objects.get(codename='view_user')
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('accounts:group_new'),
            {
                'name': 'Coordenadores',
                'permissions': [permission.pk],
            },
            HTTP_HX_REQUEST='true',
        )

        grupo = Group.objects.get(name='Coordenadores')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(grupo.permissions.filter(pk=permission.pk).exists())
        self.assertContains(response, 'Coordenadores')

    def test_modal_grupo_exibe_permissoes_em_portugues(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('accounts:group_new'), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Visualizar usuários')
        self.assertContains(response, 'O que este grupo pode fazer')

    def test_cria_usuario_atribuindo_grupo(self):
        grupo = Group.objects.create(name='Professores')
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('accounts:user_new'),
            {
                'username': 'novo',
                'first_name': 'Novo',
                'last_name': 'Usuario',
                'email': 'novo@example.com',
                'password': 'senha-forte-123',
                'is_active': 'on',
                'groups': [grupo.pk],
            },
            HTTP_HX_REQUEST='true',
        )

        usuario = User.objects.get(username='novo')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(usuario.check_password('senha-forte-123'))
        self.assertTrue(usuario.groups.filter(pk=grupo.pk).exists())
        self.assertContains(response, 'Novo Usuario')

    def test_nao_exclui_grupo_com_usuario(self):
        grupo = Group.objects.create(name='Professores')
        self.user.groups.add(grupo)
        self.client.force_login(self.staff)

        response = self.client.delete(reverse('accounts:group_delete', args=[grupo.pk]), HTTP_HX_REQUEST='true')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Group.objects.filter(pk=grupo.pk).exists())
        self.assertContains(response, 'Não é possível excluir um grupo atribuído a usuários.')
