import json

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from Model.models import Patient, RendezVous, Service
from Utilisateur.forms import ConnexionForm


# Create your views here.


class Connexion(LoginView):
    template_name = 'connexion.html'
    form_class = ConnexionForm

    def get_success_url(self):
        return reverse('Utilisateur:acceuil')

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


@login_required(login_url='Utilisateur:Connexion')
def acceuil(request):
    return render(request, 'accueil/index.html')


@login_required(login_url='Utilisateur:Connexion')
def gestion_patients(request):
    patients = Patient.objects.all()
    return render(request, 'patient/index.html', {'patients': patients})


@login_required(login_url='Utilisateur:Connexion')
def ajouter_patient(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                Patient.objects.create(
                    nom=request.POST.get('nom', '').strip(),
                    prenom=request.POST.get('prenom', '').strip(),
                    profession=request.POST.get('profession', '').strip(),
                    nationalite=request.POST.get('nationalite', '').strip(),
                    age=request.POST.get('age', '').strip(),
                    sexe=request.POST.get('sexe', '').strip(),
                    lieu_habitation=request.POST.get('lieu_habitation', '').strip(),
                    numero=request.POST.get('numero', '').strip(),
                    statut_conjugal=request.POST.get('statut_conjugal', '').strip(),
                    groupe_sanguin=request.POST.get('groupe_sanguin', '').strip(),
                )

            return JsonResponse({'success': 'Patient enregistré avec succès !'})

        except ValueError as e:
            print(f"Erreur de validation : {e}")
            return JsonResponse(
                {'error': 'Une erreur de validation est survenue. Veuillez vérifier les informations saisies.'},
                status=400
            )
        except Exception as e:
            print(f"Erreur : {e}")
            return JsonResponse(
                {'error': 'Une erreur est survenue lors de l\'enregistrement.'}, status=400
            )

    return JsonResponse({'error': 'Requête invalide.'}, status=400)


@login_required(login_url='Utilisateur:Connexion')
def gestionRdvs(request):
    user_connect = request.user
    user_role = user_connect.role.designation
    patients = Patient.objects.all()
    if user_role == "Caisse":
        rendez_vous = RendezVous.objects.all()

    elif user_role == "Medecin":
        service_medecin = user_connect.role.service
        rendez_vous = RendezVous.objects.filter(service=service_medecin)

    else:
        rendez_vous = RendezVous.objects.none()

    patients_data = list(patients.values('code_patient', 'nom'))
    context = {
        'rendez_vous': rendez_vous,
        'patients': patients,
        'patients_json': json.dumps(patients_data, cls=DjangoJSONEncoder)
    }

    return render(request, 'rdv/index.html', context)


@login_required(login_url='Utilisateur:Connexion')
def ajouter_Rdvs(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                code_patient = request.POST.get('code_patient', '').strip()
                patient = get_object_or_404(Patient, code_patient=code_patient)
                service_id = request.POST.get('service', '').strip()
                service = get_object_or_404(Service, designation=service_id)
                RendezVous.objects.create(
                    motif=request.POST.get('motif', '').strip(),
                    service=service,
                    date=request.POST.get('date', '').strip(),
                    patient=patient,
                )

            return JsonResponse({'success': 'Rendez-vous enregistré avec succès !'})

        except ValueError as e:
            print(f"Erreur de validation : {e}")
            return JsonResponse(
                {'error': 'Une erreur de validation est survenue. Veuillez vérifier les informations saisies.'},
                status=400
            )
        except Exception as e:
            print(f"Erreur : {e}")
            return JsonResponse(
                {'error': 'Une erreur est survenue lors de l\'enregistrement.'}, status=400
            )

    return JsonResponse({'error': 'Requête invalide.'}, status=400)
