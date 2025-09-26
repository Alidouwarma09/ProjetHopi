from django.urls import path
from .views import Connexion, acceuil, Deconnexion, ajouter_patient, gestion_patients, gestionRdvs, ajouter_Rdvs, \
    parametre, pharmacie, ajouter_medicament, modifier_medicament, hospitalisation, ajouter_hospitalisation, \
    consultation, ajouter_consultation, examens, ajouter_examen, pdf_consultation, enregistrer_sortie, sorties, \
    recu_sortie

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
    path('ajouter_examen/', ajouter_examen, name='ajouter_examen'),
    path('pharmacie/', pharmacie, name='pharmacie'),
    path('examens/', examens, name='examens'),
    path('hospitalisation/', hospitalisation, name='hospitalisation'),
    path('sorties/', sorties, name='sorties'),
    path('recu_sortie/<int:sortie_id>/', recu_sortie, name='recu_sortie'),
    path('enregistrer_sortie/<int:hosp_id>/', enregistrer_sortie, name='enregistrer_sortie'),
    path('consultation/', consultation, name='consultation'),
    path('gestionPatient/', gestion_patients, name='gestion_patients'),
    path('parametre/', parametre, name='parametre'),
    path('gestionRdvs/', gestionRdvs, name='gestionRdvs'),
    path('consultation/<int:consultation_id>/pdf/', pdf_consultation, name='pdf_consultation'),
    path('modifier_medicament/', modifier_medicament, name='modifier_medicament'),
]
