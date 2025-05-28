from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse

from Utilisateur.forms import ConnexionForm


# Create your views here.


class Connexion(LoginView):
    template_name = 'connexion.html'
    form_class = ConnexionForm

    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse('Utilisateur:acceuil')
        return reverse('Utilisateur:Connexion')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


# def page_blocage(request):
#     return render(request, 'blocage/index.html')


def Deconnexion(request):
    logout(request)
    return redirect(reverse('Utilisateur:Connexion'))


@login_required(login_url='Utilisateur:Connexion')
def acceuil(request):
    return render(request, 'accueil/index.html')
