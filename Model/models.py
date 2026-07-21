import string
import random

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from datetime import date, timedelta

from django.db.models import UniqueConstraint

from decimal import Decimal

from django.utils import timezone


class MyUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Vous devez entrer un nom d'utilisateur")

        user = self.model(
            username=username,
            **extra_fields  # Ajout des champs supplémentaires
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None):
        user = self.create_user(username=username, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user

    def create_admin(self, username, email, nom, prenom, roles, password=None):
        if not username:
            raise ValueError("Vous devez entrer un nom d'utilisateur")
        if not email:
            raise ValueError("Vous devez entrer un email")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            nom=nom,
            prenom=prenom,
            roles=roles
        )
        user.set_password(password)
        user.is_staff = True
        user.is_admin = True
        user.save(using=self._db)
        return user


class Service(models.Model):
    designation = models.CharField(max_length=100)

    def __str__(self):
        return self.designation


class Role(models.Model):
    designation = models.CharField(max_length=100)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='roless')

    def __str__(self):
        return f"{self.designation} - {self.service.designation}"


class Utilisateur(AbstractBaseUser):
    username = models.CharField(
        unique=True,
        max_length=255,
        blank=False
    )
    nom = models.CharField(max_length=250, verbose_name='nom')
    prenom = models.CharField(max_length=250)
    last_activity = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='utilisateurs')
    USERNAME_FIELD = 'username'
    objects = MyUserManager()

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    def est_en_ligne(self):
        """
        Retourne un dictionnaire avec l'état en ligne et la dernière connexion.
        """
        now = timezone.now()
        delta = now - self.last_activity
        en_ligne = delta <= timedelta(minutes=2)  # seuil pour considérer l'utilisateur en ligne

        return {
            'en_ligne': en_ligne,
            'derniere_connexion': self.last_activity,  # datetime
        }


class Patient(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    nationalite = models.CharField(max_length=100)
    age = models.DecimalField(max_digits=10, decimal_places=0)
    sexe = models.CharField(max_length=10)
    lieu_habitation = models.TextField(blank=True)
    numero = models.CharField(max_length=20)
    statut_conjugal = models.CharField(max_length=40)
    groupe_sanguin = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    code_patient = models.CharField(max_length=6, unique=True, editable=False, blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    def save(self, *args, **kwargs):
        if not self.code_patient:
            self.code_patient = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(characters, k=6))
            if not Patient.objects.filter(code_patient=code).exists():
                return code


class Antecedent(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='antecedents')
    ant_med = models.CharField(blank=True, null=True, max_length=250)
    ant_mal = models.CharField(blank=True, null=True, max_length=250)
    ant_chirur = models.CharField(blank=True, null=True, max_length=250)

    def __str__(self):
        return f"Antécédent de {self.patient}"


# -----------------------
# RENDEZ-VOUS
# -----------------------

class RendezVous(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='rendezvous')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='rendezvousSer')
    motif = models.CharField(blank=True, null=True, max_length=250)
    date = models.DateTimeField()

    def __str__(self):
        return f"RDV de {self.patient} le {self.date}"

    @property
    def est_passe(self):

        if self.date:
            return self.date < timezone.now()
        return False


# -----------------------
# CONSULTATIONS
# -----------------------

class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='consultations_s')
    motif = models.CharField(blank=True, null=True, max_length=250)
    poids = models.DecimalField(max_digits=10, decimal_places=2)
    taille = models.DecimalField(max_digits=10, decimal_places=2)
    IMC = models.DecimalField(max_digits=10, decimal_places=2)
    pouls = models.DecimalField(max_digits=10, decimal_places=2)
    TA = models.DecimalField(max_digits=10, decimal_places=2)
    diagnostic = models.CharField(blank=True, null=True, max_length=250)
    constat_consultation = models.CharField(blank=True, null=True, max_length=250)
    examen_demande = models.CharField(blank=True, null=True, max_length=250)
    traitement = models.CharField(blank=True, null=True, max_length=250)
    issue_consultation = models.CharField(blank=True, null=True, max_length=250)
    resultat_examen = models.CharField(blank=True, null=True, max_length=250)
    statue = models.CharField(blank=True, null=True, max_length=250)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation de {self.patient} le {self.date}"


# -----------------------
# REÇUS
# -----------------------

class Recu(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='recus', null=True,
                                     blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    monnaie = models.DecimalField(max_digits=10, decimal_places=2)
    details = models.CharField(max_length=350)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reçu {self.id} - {self.patient}"


# -----------------------
# HOSPITALISATION
# -----------------------
class Hospitalisation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='hospitalisations')
    motif = models.CharField(blank=True, null=True, max_length=250)
    diagnotic = models.CharField(blank=True, null=True, max_length=550)
    decision = models.CharField(blank=True, null=True, max_length=250)
    traitement = models.CharField(blank=True, null=True, max_length=250)
    examen = models.CharField(blank=True, null=True, max_length=250)
    details = models.CharField(blank=True, null=True, max_length=250)
    statut = models.CharField(blank=True, null=True, max_length=250)
    type = models.CharField(blank=True, null=True, max_length=250)
    info_supp = models.CharField(blank=True, null=True, max_length=250)

    def __str__(self):
        return f"Hospitalisation de {self.patient}"


class Examen(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="examens")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="examens", null=True, blank=True)
    type_examen = models.CharField(max_length=200)  # Ex: "Biologie", "Radio", "Scanner"
    resultat = models.TextField(blank=True, null=True)
    date_examen = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=50, choices=[
        ('En attente', 'En attente'),
        ('Terminé', 'Terminé')
    ], default='En attente')

    def __str__(self):
        return f"Examen {self.type_examen} - {self.patient.nom} {self.patient.prenom}"


# -----------------------
# ORDONNANCE / ARRET / BULLETIN
# -----------------------


class Medicament(models.Model):
    designation = models.CharField(max_length=100)
    date_expiration = models.DateField()
    stock = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    prix = models.IntegerField()
    type_medicament = models.CharField(max_length=100)


class Ordonnance(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='ordonnances')
    contenu = models.CharField(blank=True, null=True, max_length=250)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ordonnance pour {self.consultation}"


class Prestation(models.Model):
    recu = models.ForeignKey(Recu, on_delete=models.CASCADE, related_name='bulletins')
    designation = models.CharField(max_length=100)
    prix = models.IntegerField()


class ArretTravail(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='arrets')
    nombre_jours = models.IntegerField()
    date_debut = models.DateField()
    nom_med = models.CharField(blank=True, null=True, max_length=250)

    def __str__(self):
        return f"Arrêt de travail ({self.nombre_jours} jours) pour {self.consultation}"


class Sortie(models.Model):
    hospitalisation = models.OneToOneField(Hospitalisation, on_delete=models.CASCADE, related_name="sortie")
    date_sortie = models.DateTimeField(default=timezone.now)
    observation = models.TextField(blank=True, null=True)  # Notes médicales ou raison de la sortie
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # montant payé
    recu = models.OneToOneField(Recu, on_delete=models.SET_NULL, null=True, blank=True, related_name="sortie")

    def __str__(self):
        return f"Sortie de {self.hospitalisation.patient.nom} {self.hospitalisation.patient.prenom} - {self.date_sortie}"

    @property
    def montant_total_formate(self):
        """Formate le montant total avec des espaces comme séparateurs de milliers (ex: 100 000.00)."""
        # Conversion du décimal en entier si pas de décimales, ou formatage standard
        montant_int = int(self.montant_total)
        # Utilisation du formatage avec espace pour les milliers
        formatted_int = f"{montant_int:,}".replace(",", " ")

        # Récupération de la partie décimale
        decimaux = f"{self.montant_total:.2f}".split(".")[1]

        if decimaux == "00":
            return f"{formatted_int} FCFA"
        return f"{formatted_int},{decimaux} FCFA"
