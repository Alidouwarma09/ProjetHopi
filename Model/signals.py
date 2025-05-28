# Model/signals.py

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Utilisateur, Role, Service


@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    if not Utilisateur.objects.filter(username='SuperUser').exists():
        service, _ = Service.objects.get_or_create(designation='Urgence')
        role, _ = Role.objects.get_or_create(designation='ADMIN', service=service)

        Utilisateur.objects.create_user(
            username='SuperUser',
            password='09102079Darius',
            nom='SuperUser',
            prenom='Super',
            role=role,
            is_admin=True,
            is_staff=True,
        )
        print("Utilisateur admin créé avec succès !")
    else:
        print("Cet utilisateur existe déjà")
