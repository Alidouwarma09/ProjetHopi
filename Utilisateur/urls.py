from django.urls import path
from .views import Connexion, acceuil, Deconnexion

app_name = 'Utilisateur'
urlpatterns = [
    path('', Connexion.as_view(), name='Connexion'),
    path('Deconnexion/', Deconnexion, name='Deconnexion'),
    path('acceuil/', acceuil, name='acceuil'),
]
