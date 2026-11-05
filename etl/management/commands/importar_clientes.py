from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from etl.pipeline import executar


class Command(BaseCommand):
    help = "Importa um CSV de clientes da Distribuidora Vetor (extrair, transformar, carregar)."

    def add_arguments(self, parser):
        parser.add_argument(
            "arquivo",
            help="Caminho do CSV, ex.: dados/clientes_distribuidora_vetor.csv",
        )

    def handle(self, *args, **opcoes):
        caminho = Path(opcoes["arquivo"])
        if not caminho.exists():
            raise CommandError(f"Arquivo não encontrado: {caminho}")

        execucao = executar(caminho, caminho.name)

        if not execucao.sucesso:
            raise CommandError(execucao.mensagem)

        self.stdout.write(
            self.style.SUCCESS(
                f"Lidas: {execucao.lidas} | Carregadas: {execucao.carregadas} | "
                f"Em Revisão: {execucao.em_revisao} | Descartadas: {execucao.descartadas} | "
                f"{execucao.mensagem}"
            )
        )
