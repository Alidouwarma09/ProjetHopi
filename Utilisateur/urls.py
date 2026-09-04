from django.urls import path
from .views import Connexion, acceuil, Deconnexion, ajouter_patient, gestion_patients, gestionRdvs, ajouter_Rdvs, \
    parametre, pharmacie, ajouter_medicament, modifier_medicament, hospitalisation, ajouter_hospitalisation, \
    consultation, ajouter_consultation, examens, ajouter_examen, pdf_consultation, enregistrer_sortie, sorties, \
    recu_sortie, modifier_patient, supprimer_patient, supprimer_Rdvs, modifier_Rdvs, modifier_consultation, \
    supprimer_consultation, gestion_utilisateur, ajouter_utilisateur, export_utilisateurs_pdf, supprimer_user, \
    modifier_utilisateur, modifier_profil, carte_patient, pdf_arret, pdf_ordonnance, get_derniere_consultation, \
    recu_consultation

app_name = 'Utilisateur'
urlpatterns = [
    path('', acceuil, name='acceuil'),
    path('Connexion/', Connexion.as_view(), name='Connexion'),
    path('Deconnexion/', Deconnexion, name='Deconnexion'),
    path('ajouter/', ajouter_patient, name='ajouter_patient'),
    path('ajouter_utilisateur/', ajouter_utilisateur, name='ajouter_utilisateur'),
    path('ajouter_Rdvs/', ajouter_Rdvs, name='ajouter_Rdvs'),
    path('ajouter_hospitalisation/', ajouter_hospitalisation, name='ajouter_hospitalisation'),
    path('ajouter_consultation/', ajouter_consultation, name='ajouter_consultation'),
    path('ajouter_medicament/', ajouter_medicament, name='ajouter_medicament'),
    path('ajouter_examen/', ajouter_examen, name='ajouter_examen'),
    path('pharmacie/', pharmacie, name='pharmacie'),
    path('gestion_utilisateur/', gestion_utilisateur, name='gestion_utilisateur'),
    path('export_utilisateurs_pdf/', export_utilisateurs_pdf, name='export_utilisateurs_pdf'),
    path('examens/', examens, name='examens'),
    path('hospitalisation/', hospitalisation, name='hospitalisation'),
    path('sorties/', sorties, name='sorties'),
    path('recu_sortie/<int:sortie_id>/', recu_sortie, name='recu_sortie'),
    path('carte/<int:patient_id>/', carte_patient, name='carte_patient'),
    path('enregistrer_sortie/<int:hosp_id>/', enregistrer_sortie, name='enregistrer_sortie'),
    path('consultation/', consultation, name='consultation'),
    path('gestionPatient/', gestion_patients, name='gestion_patients'),
    path('parametre/', parametre, name='parametre'),
    path('gestionRdvs/', gestionRdvs, name='gestionRdvs'),
    path('consultation/<int:consultation_id>/pdf/', pdf_consultation, name='pdf_consultation'),
    path('modifier_medicament/', modifier_medicament, name='modifier_medicament'),
    path('modifier_patient/', modifier_patient, name='modifier_patient'),
    path('supprimer_patient/<int:id>/', supprimer_patient, name='supprimer_patient'),
    path('modifier_Rdvs/<int:id>/', modifier_Rdvs, name='modifier_Rdvs'),
    path('supprimer_Rdvs/<int:id>/', supprimer_Rdvs, name='supprimer_Rdvs'),
    path('modifier_consultation/<int:id>/', modifier_consultation, name='modifier_consultation'),
    path('supprimer_consultation/<int:id>/', supprimer_consultation, name='supprimer_consultation'),
    path('supprimer_user/<int:id>/', supprimer_user, name='supprimer_user'),
    path('modifier_utilisateur/<int:id>/', modifier_utilisateur, name='modifier_utilisateur'),
    path('modifier_profil/', modifier_profil, name='modifier_profil'),
    path('pdf_arret/<int:consultation_id>/', pdf_arret, name='pdf_arret'),
    path('pdf_ordonnance/<int:consultation_id>/', pdf_ordonnance, name='pdf_ordonnance'),
    path('get_derniere_consultation/<str:code_patient>/', get_derniere_consultation, name='get_derniere_consultation'),
    path('recu_consultation/<int:consultation_id>/', recu_consultation, name='recu_consultation'),

]
