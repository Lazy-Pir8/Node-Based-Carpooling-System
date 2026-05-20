from allauth.account.signals import user_signed_up
from django.dispatch import receiver


@receiver(user_signed_up)
def handle_social_signup(request, user, **kwargs):
    """
    After Google (or any social) sign-up:
    - ensure a sensible username
    - leave role=None so onboarding is triggered
    """
    if not user.username:
        user.username = f"user_{user.id}"
    user.role = None  # Force onboarding
    user.save()
