from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Utilisateur, Role, Service


@receiver(post_migrate)
def create_default_services_and_admin(sender, **kwargs):
    # 1. Liste de tous les services par défaut à créer
    default_services = [
        "Urgences",
        "Pédiatrie",
        "Gynécologie / Obstétrique",
        "Médecine générale",
        "Chirurgie",
        "Cardiologie",
        "Neurologie",
        "Dermatologie",
        "Ophtalmologie",
        "Orthopédie",
        "Radiologie / Imagerie",
        "Oncologie",
        "Anesthésie / Réanimation",
        "Psychiatrie",
        "ORL",
        "Urologie",
        "Laboratoire",
        "Pharmacie",
        "Stomatologie / Odontologie",
    ]

    services_objects = {}

    for designation in default_services:
        service_obj, created = Service.objects.get_or_create(designation=designation)
        services_objects[designation] = service_obj
        if created:
            print(f"Service créé : {designation}")

    if not Utilisateur.objects.filter(username='SuperUser').exists():
        service_admin = services_objects.get("Urgences")

        if not service_admin:
            service_admin, _ = Service.objects.get_or_create(designation="Urgences")

        role, _ = Role.objects.get_or_create(designation='ADMIN', service=service_admin)

        Utilisateur.objects.create_user(
            username='SuperUser',
            password='12345678',
            nom='SuperUser',
            prenom='Super',
            role=role,
            is_admin=True,
            is_staff=True,
        )
        print("Utilisateur admin créé avec succès !")
    else:
        print("L'utilisateur admin 'SuperUser' existe déjà")