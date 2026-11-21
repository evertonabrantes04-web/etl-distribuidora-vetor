from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models.functions import Lower

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if user.email:
            user.email = user.email.strip().lower()
        return user

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = (sociallogin.user.email or "").strip().lower()
        if not email and sociallogin.email_addresses:
            email = (sociallogin.email_addresses[0].email or "").strip().lower()

        if not email:
            return

        sociallogin.user.email = email
        for email_obj in sociallogin.email_addresses:
            if email_obj.email:
                email_obj.email = email_obj.email.strip().lower()

        extra_data = sociallogin.account.extra_data or {}
        email_verificado = (
            any(e.verified for e in sociallogin.email_addresses)
            or bool(extra_data.get("email_verified"))
            or sociallogin.account.provider == "microsoft"
        )

        if not email_verificado:
            messages.warning(
                request,
                "O e-mail não está verificado no provedor selecionado. "
                "Entre com sua senha ou verifique o e-mail antes de vincular.",
            )
            return

        usuario_existente = (
            User.objects.annotate(email_lower=Lower("email"))
            .filter(email_lower=email)
            .order_by("-is_active", "date_joined", "id")
            .first()
        )

        if usuario_existente:
            sociallogin.connect(request, usuario_existente)
            provedor = sociallogin.account.provider.capitalize()
            messages.info(
                request,
                f"Sua conta {provedor} foi vinculada automaticamente ao cadastro existente.",
            )