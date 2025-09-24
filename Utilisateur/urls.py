from django.urls import path
from .views import Connexion, acceuil, Deconnexion, ajouter_patient, gestion_patients, gestionRdvs, ajouter_Rdvs, \
    parametre, pharmacie, ajouter_medicament, modifier_medicament, hospitalisation, ajouter_hospitalisation, \
    consultation, ajouter_consultation

app_name = 'Utilisateur'
urlpatterns = [
    path('', acceuil, name='acceuil'),
    path('Connexion/', Connexion.as_view(), name='Connexion'),
    path('Deconnexion/', Deconnexion, name='Deconnexion'),
    path('ajouter/', ajouter_patient, name='ajouter_patient'),
    path('ajouter_Rdvs/', ajouter_Rdvs, name='ajouter_Rdvs'),
    path('ajouter_hospitalisation/', ajouter_hospitalisation, name='ajouter_hospitalisation'),
    path('ajouter_consultation/', ajouter_consultation, name='ajouter_consultation'),
    path('ajouter_medicament/', ajouter_medicament, name='ajouter_medicament'),
    path('pharmacie/', pharmacie, name='pharmacie'),
    path('hospitalisation/', hospitalisation, name='hospitalisation'),
    path('consultation/', consultation, name='consultation'),
    path('gestionPatient/', gestion_patients, name='gestion_patients'),
    path('parametre/', parametre, name='parametre'),
    path('gestionRdvs/', gestionRdvs, name='gestionRdvs'),
    path('modifier_medicament/', modifier_medicament, name='modifier_medicament'),
]
