from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.reservations.constants import ReservaStatus
from apps.reservations.models import Reserva
from apps.rooms.models import Recurso, Sala


class Command(BaseCommand):
    help = "Seed database with the same mock data used in the frontend server.ts."

    def handle(self, *args, **options):
        recursos_map = self._seed_resources()
        salas_map = self._seed_rooms(recursos_map)
        user = self._get_seed_user()
        self._seed_bookings(salas_map, user)
        self.stdout.write(self.style.SUCCESS("Seed concluido com sucesso."))

    def _seed_resources(self):
        frontend_resources = [
            {"id": "proj", "name": "4K Projector", "qty": 5, "icon": "videocam"},
            {"id": "tv", "name": "Smart TV 65\"", "qty": 12, "icon": "tv"},
            {"id": "board", "name": "Glass Whiteboard", "qty": 8, "icon": "edit_note"},
            {"id": "local_cafe", "name": "Local Cafe", "qty": 1, "icon": "local_cafe"},
        ]
        recursos_map = {}
        for recurso in frontend_resources:
            obj, _created = Recurso.objects.get_or_create(
                nome=recurso["name"],
                defaults={
                    "descricao": f"Icone: {recurso['icon']} | Quantidade: {recurso['qty']}",
                    "ativo": True,
                },
            )
            recursos_map[recurso["icon"]] = obj
        return recursos_map

    def _seed_rooms(self, recursos_map):
        frontend_rooms = [
            {
                "id": "boardroom-a",
                "name": "Boardroom Alpha & A",
                "capacity": 12,
                "status": "occupied",
                "predio": "Workspace Portal",
                "andar": 1,
                "image": "https://lh3.googleusercontent.com/aida-public/AB6AXuAQB7l6M1s0CAjAyDxn43720bwv37d1PR3oLmMHwUjzevN8uaOIs48NAxlN9zueFQY-KzXNZvyQ2Fdni439Gc__o9IdF9KRgz0KmExVIrMC7o2WQCMkVl5Awkowlzawh4D0uDvwfsrn7gkE29NsDC0wHaZWvR-mqm0GZlsWIqzgJ3rMPqe0acdIULNuWfm4kigkt-sRAzS4BYLQtCV-DTD_286pfk6qDANynobRZiF7EcJpT7kqspVaatKlC3CWbjrT7fIUOCzmVpru",
                "equipment": ["videocam", "edit_note", "local_cafe"],
            },
            {
                "id": "huddle-1",
                "name": "Huddle Room 1",
                "capacity": 4,
                "status": "occupied",
                "predio": "Workspace Portal",
                "andar": 2,
                "image": "https://lh3.googleusercontent.com/aida-public/AB6AXuDnIjJr43gVPqmiSbt2iPaw34cOdKngWsWsETYoH029pulblFKe92WIwSMSpHIz4UIM5AxrgZYY7q3L0yn5nsqbji5XcUA7zPsL7oWJsJ_WpCLPbR0h2PFoMKbFZErBjPQzIkY695KOpVDd5-yP60zVVRc9ImQf9Qec_eMQ0X5InMkIfCtRjQPrI6_yCyqVFpOSdZMJaF3-kunYYzHNVrJsaP0tOy06H1upFiZuDT9wJvRrQhugxaW_PbpRdwCng9FRpEMcAakZG9KF",
                "equipment": ["tv", "edit_note"],
            },
            {
                "id": "studio-b",
                "name": "Studio B",
                "capacity": 8,
                "status": "available",
                "predio": "Workspace Portal",
                "andar": 3,
                "image": "https://lh3.googleusercontent.com/aida-public/AB6AXuAWojhQV4tHPXBwK2Eg-vjB0Kgq3iT7Sv5TmsIq92P7QXLLh772nRonO1yPvd042F2r0xx2hGSu1gxLGvRjPvs0WosoJ8mQteK3vvV40SBSK9vSYI7qfrl-OMg8TPGQDPXI-ZEoK7yKIKMpDnlml2bRsKy5pGnZ2D6GY3kWs3S-UgCGY6BN_LFRG2pBjd_4NXc4w0Nlpw89Kd-O867KHRZmT_PWabbBrBT-nZ2d1H7nrfsPpB6Ab8MPql2OsIkDaESc-kdH7SSi9HUc",
                "equipment": ["videocam"],
            },
        ]

        salas_map = {}
        for sala in frontend_rooms:
            obj, _created = Sala.objects.get_or_create(
                nome=sala["name"],
                predio=sala["predio"],
                andar=sala["andar"],
                defaults={
                    "capacidade": sala["capacity"],
                    "descricao": f"Imagem: {sala['image']} | Status: {sala['status']}",
                    "ativa": True,
                },
            )
            obj.capacidade = sala["capacity"]
            obj.descricao = f"Imagem: {sala['image']} | Status: {sala['status']}"
            obj.ativa = True
            obj.save(update_fields=["capacidade", "descricao", "ativa"])
            obj.recursos.set([recursos_map[eq] for eq in sala["equipment"] if eq in recursos_map])
            salas_map[sala["id"]] = obj
        return salas_map

    def _get_seed_user(self):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="frontend.seed",
            defaults={"first_name": "Frontend", "last_name": "Seed"},
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
        return user

    def _seed_bookings(self, salas_map, user):
        frontend_bookings = [
            {
                "id": "book-1",
                "title": "Executive Q3 Review",
                "date": "2026-05-31",
                "startTime": "10:00 AM",
                "endTime": "11:30 AM",
                "room": "boardroom-a",
                "equipment": ["videocam", "edit_note"],
            },
            {
                "id": "book-2",
                "title": "Sync diario focado",
                "date": "2026-05-31",
                "startTime": "09:00 AM",
                "endTime": "10:00 AM",
                "room": "huddle-1",
                "equipment": ["edit_note"],
            },
            {
                "id": "book-3",
                "title": "Entrevistas de Contratacao",
                "date": "2026-05-31",
                "startTime": "12:00 PM",
                "endTime": "01:00 PM",
                "room": "huddle-1",
                "equipment": ["tv"],
            },
        ]

        for booking in frontend_bookings:
            sala = salas_map.get(booking["room"])
            if not sala:
                continue
            data = datetime.strptime(booking["date"], "%Y-%m-%d").date()
            hora_inicio = datetime.strptime(booking["startTime"], "%I:%M %p").time()
            hora_fim = datetime.strptime(booking["endTime"], "%I:%M %p").time()
            Reserva.objects.get_or_create(
                sala=sala,
                professor=user,
                data=data,
                hora_inicio=hora_inicio,
                hora_fim=hora_fim,
                defaults={
                    "titulo": booking["title"],
                    "status": ReservaStatus.ATIVA,
                },
            )
