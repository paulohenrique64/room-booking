from django.core.management.base import BaseCommand

from load import populate


class Command(BaseCommand):
    help = 'Popula o banco com dados de demonstração para salas, equipamentos e reservas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove reservas, salas e equipamentos antes de popular.',
        )

    def handle(self, *args, **options):
        populate(clear=options['limpar'], stdout=self.stdout.write)
        self.stdout.write(self.style.SUCCESS('Dados de demonstração criados com sucesso.'))
