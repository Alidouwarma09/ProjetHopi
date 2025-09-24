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
from datetime import timedelta, datetime, date

from django.views.decorators.csrf import csrf_exempt

from Model.models import Patient, RendezVous, Service, Medicament, Hospitalisation, Consultation
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


def parametre(request):
    return render(request, 'parametre/index.html')


@login_required(login_url='Utilisateur:Connexion')
def acceuil(request):
    il_y_a_une_semaine = datetime.now() - timedelta(days=7)
    stats_patient = Patient.objects.filter(created_at__gte=il_y_a_une_semaine).count()
    patients = Patient.objects.order_by('-id')[:10]
    for patient in patients:
        print(patient.id)

    return render(request, 'accueil/index.html', {'patients': patients, 'stats_patient': stats_patient})


@login_required(login_url='Utilisateur:Connexion')
def pharmacie(request):
    today = date.today()
    medicaments = Medicament.objects.all()
    nombre_medicament = Medicament.objects.all().count()
    nombre_rupture = Medicament.objects.filter(stock=0).count()
    medicaments_expire = Medicament.objects.filter(date_expiration__lte=today).count()
    faible_stock = Medicament.objects.filter(stock__lte=30).count()
    return render(request, 'pharmacie/index.html', {'medicaments': medicaments,
                                                    'nombre_medicament': nombre_medicament,
                                                    'nombre_rupture': nombre_rupture,
                                                    'medicaments_expire': medicaments_expire,
                                                    'faible_stock': faible_stock})


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
    if user_role == "CAISSE":
        rendez_vous = RendezVous.objects.all()

    elif user_role == "MEDECIN":
        service_medecin = user_connect.role.service
        rendez_vous = RendezVous.objects.filter(service=service_medecin)
    elif user_role == "ADMIN":
        rendez_vous = RendezVous.objects.all()

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
def hospitalisation(request):
    hospitalisations = Hospitalisation.objects.all().select_related('patient')
    patients = Patient.objects.all()
    return render(request, 'hospitalisation/index.html', {
        'hospitalisations': hospitalisations,
        'patients': patients
    })


@login_required(login_url='Utilisateur:Connexion')
def consultation(request):
    consultations = Consultation.objects.all().select_related('patient', 'service')
    patients = Patient.objects.all()
    services = Service.objects.all()
    return render(request, 'consultation/index.html', {
        'consultations': consultations,
        'patients': patients,
        'services': services
    })


@login_required(login_url='Utilisateur:Connexion')
def ajouter_medicament(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                designation = request.POST.get('designation', '').strip()
                type_medicament = request.POST.get('type_medicament', '').strip()
                prix = request.POST.get('prix', '').strip()
                stock = request.POST.get('stock', '').strip()
                date_expiration = request.POST.get('date_expiration', '').strip()
                print(date_expiration)
                code = request.POST.get('code', '').strip()

                Medicament.objects.create(
                    designation=designation,
                    type_medicament=type_medicament,
                    stock=stock,
                    code=code,
                    date_expiration=date_expiration,
                    prix=prix,
                )

            return JsonResponse({'success': 'Medicament enregistré avec succès !'})

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
def ajouter_hospitalisation(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Récupération des données du formulaire
                code_patient = request.POST.get('code_patient', '').strip()
                patient = get_object_or_404(Patient, code_patient=code_patient)

                motif = request.POST.get('motif', '').strip()
                diagnostic = request.POST.get('diagnostic', '').strip()
                decision = request.POST.get('decision', '').strip()
                traitement = request.POST.get('traitement', '').strip()
                examen = request.POST.get('examen', '').strip()
                details = request.POST.get('details', '').strip()
                statut = request.POST.get('statut', '').strip()
                type_hosp = request.POST.get('type', '').strip()
                info_supp = request.POST.get('info_supp', '').strip()

                # Création de l'hospitalisation
                Hospitalisation.objects.create(
                    patient=patient,
                    motif=motif,
                    diagnotic=diagnostic,
                    decision=decision,
                    traitement=traitement,
                    examen=examen,
                    details=details,
                    statut=statut,
                    type=type_hosp,
                    info_supp=info_supp
                )

            return JsonResponse({'success': 'Hospitalisation enregistrée avec succès !'})

        except ValueError as e:
            print(f"Erreur de validation : {e}")
            return JsonResponse(
                {'error': 'Une erreur de validation est survenue. Veuillez vérifier les informations saisies.'},
                status=400
            )

    return JsonResponse({'error': 'Requête invalide.'}, status=400)


@login_required(login_url='Utilisateur:Connexion')
def ajouter_consultation(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Récupération des données du formulaire
                code_patient = request.POST.get('code_patient', '').strip()
                patient = get_object_or_404(Patient, code_patient=code_patient)

                service_id = request.POST.get('service', '').strip()
                service = get_object_or_404(Service, id=service_id)

                motif = request.POST.get('motif', '').strip()
                poids = request.POST.get('poids', '0').strip()
                taille = request.POST.get('taille', '0').strip()
                IMC = request.POST.get('IMC', '0').strip()
                pouls = request.POST.get('pouls', '0').strip()
                TA = request.POST.get('TA', '0').strip()
                diagnostic = request.POST.get('diagnostic', '').strip()
                constat_consultation = request.POST.get('constat_consultation', '').strip()
                examen_demande = request.POST.get('examen_demande', '').strip()
                traitement = request.POST.get('traitement', '').strip()
                issue_consultation = request.POST.get('issue_consultation', '').strip()
                resultat_examen = request.POST.get('resultat_examen', '').strip()
                statue = request.POST.get('statue', '').strip()

                # Création de la consultation
                Consultation.objects.create(
                    patient=patient,
                    service=service,
                    motif=motif,
                    poids=poids,
                    taille=taille,
                    IMC=IMC,
                    pouls=pouls,
                    TA=TA,
                    diagnostic=diagnostic,
                    constat_consultation=constat_consultation,
                    examen_demande=examen_demande,
                    traitement=traitement,
                    issue_consultation=issue_consultation,
                    resultat_examen=resultat_examen,
                    statue=statue
                )

            return JsonResponse({'success': 'Consultation enregistrée avec succès !'})

        except ValueError as e:
            print(f"Erreur de validation : {e}")
            return JsonResponse(
                {'error': 'Une erreur de validation est survenue. Veuillez vérifier les informations saisies.'},
                status=400
            )
        except Exception as e:
            print(f"Erreur : {e}")
            return JsonResponse(
                {'error': 'Une erreur est survenue lors de l\'enregistrement.'},
                status=400
            )

    return JsonResponse({'error': 'Requête invalide.'}, status=400)


@login_required(login_url='Utilisateur:Connexion')
def ajouter_Rdvs(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                code_patient = request.POST.get('code_patient', '').strip()
                patient = get_object_or_404(Patient, code_patient=code_patient)

                service_id = request.POST.get('service', '').strip()

                service = get_object_or_404(Service, designation=service_id)
                print('service:', service)

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


@csrf_exempt
def modifier_medicament(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # <-- récupère le JSON
            medicament_id = data.get('id')
            stock = data.get('stock')

            medicament = Medicament.objects.get(id=medicament_id)
            medicament.stock = stock
            medicament.save()
            return JsonResponse({'success': 'Stock mis à jour avec succès !'})

        except Medicament.DoesNotExist:
            return JsonResponse({'error': 'Médicament introuvable.'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Données JSON invalides.'})

    return JsonResponse({'error': 'Requête invalide.'})
