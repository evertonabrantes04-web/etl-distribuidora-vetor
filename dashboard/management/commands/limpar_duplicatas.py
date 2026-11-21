from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import Lower

User = get_user_model()


class Command(BaseCommand):
    help = "Identifica, mescla e limpa usuários duplicados por e-mail (case-insensitive)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a limpeza no terminal sem alterar o SQLite.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("=== MODO SIMULAÇÃO (--dry-run): Nenhuma alteração será gravada ===\n")
            )

        grupos = list(
            User.objects.exclude(email__isnull=True)
            .exclude(email__exact="")
            .annotate(email_lower=Lower("email"))
            .values("email_lower")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        if not grupos:
            self.stdout.write(self.style.SUCCESS("Nenhum usuário duplicado encontrado."))
            return

        total_removidos = 0
        total_sociais = 0

        for grupo in grupos:
            email_norm = grupo["email_lower"].strip().lower()
            usuarios = list(
                User.objects.annotate(email_lower=Lower("email"))
                .filter(email_lower=email_norm)
                .order_by("-is_active", "-is_superuser", "-is_staff", "date_joined", "id")
            )

            principal = usuarios[0]
            duplicados = usuarios[1:]

            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"E-mail: {email_norm} | Principal: ID={principal.id} ({principal.username})"
                )
            )

            if dry_run:
                for dup in duplicados:
                    qtd_social = SocialAccount.objects.filter(user=dup).count()
                    qtd_logs = LogEntry.objects.filter(user=dup).count()
                    self.stdout.write(
                        f"  [SIMULAÇÃO] Removeria ID={dup.id} ({dup.username}) | "
                        f"SocialAccounts: {qtd_social} | Logs do Admin: {qtd_logs}"
                    )
                continue

            with transaction.atomic():
                algum_verificado = EmailAddress.objects.filter(
                    user__in=usuarios,
                    email__iexact=email_norm,
                    verified=True,
                ).exists()

                for dup in duplicados:
                    # 1. Transfere contas Google/Microsoft vinculadas
                    for sa in SocialAccount.objects.filter(user=dup):
                        ja_existe = SocialAccount.objects.filter(
                            user=principal,
                            provider=sa.provider,
                            uid=sa.uid,
                        ).exists()
                        if ja_existe:
                            sa.delete()
                        else:
                            sa.user = principal
                            sa.save(update_fields=["user"])
                            total_sociais += 1

                    # 2. Preserva o histórico de auditoria do Django Admin
                    LogEntry.objects.filter(user=dup).update(user=principal)

                    # 3. Se no futuro adicionar ForeignKey para User em etl.models.Execucao,
                    # transfira aqui antes de apagar o duplicado:
                    # Execucao.objects.filter(usuario=dup).update(usuario=principal)

                    EmailAddress.objects.filter(user=dup).delete()
                    dup_id, dup_user = dup.id, dup.username
                    dup.delete()
                    total_removidos += 1

                    self.stdout.write(
                        self.style.SUCCESS(f"  [OK] ID={dup_id} ({dup_user}) mesclado e removido.")
                    )

                if principal.email != email_norm:
                    principal.email = email_norm
                    principal.save(update_fields=["email"])

                EmailAddress.objects.filter(user=principal, email__iexact=email_norm).delete()
                EmailAddress.objects.create(
                    user=principal,
                    email=email_norm,
                    primary=True,
                    verified=algum_verificado,
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nLimpeza concluída! Removidos: {total_removidos} | "
                    f"Contas sociais transferidas: {total_sociais}."
                )
            )