import json
import os
import tempfile
import uuid
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.views import LoginView
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Case, When, IntegerField, Value, FloatField, BooleanField
from django.db.models.functions import Cast
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime, date

from django.views.decorators.csrf import csrf_exempt
from six import BytesIO
from weasyprint import HTML

from Model.models import Patient, RendezVous, Service, Medicament, Hospitalisation, Consultation, Examen, Ordonnance, \
    ArretTravail, Recu, Prestation, Sortie, Antecedent, Utilisateur, Role
from Utilisateur.forms import ConnexionForm
from django.db import models


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

    # Patients récents
    patients = Patient.objects.order_by('-id')[:10]

    # Nouveaux patients créés cette semaine
    stats_patient = Patient.objects.filter(created_at__gte=il_y_a_une_semaine).count()

    # Hospitalisations récentes
    hospitalisations_recentes = Hospitalisation.objects.select_related('patient').order_by('-id')[:10]

    # Médicaments récents
    medicaments_recents = Medicament.objects.order_by('-id')[:8]

    # Médicaments avec le stock le plus faible (conversion du champ stock en float)
    medicaments_stock_bas = (
        Medicament.objects
            .annotate(stock_num=Cast('stock', FloatField()))
            .order_by('stock_num')[:5]
    )

    # Statistiques utilisateurs par service
    stats_services = (
        Utilisateur.objects.values('role__designation')
            .annotate(nombre=models.Count('id'))
    )

    return render(request, 'accueil/index.html', {
        'patients': patients,
        'stats_patient': stats_patient,
        'hospitalisations_recentes': hospitalisations_recentes,
        'medicaments_recents': medicaments_recents,
        'medicaments_stock_bas': medicaments_stock_bas,
        'stats_services': list(stats_services),
    })


@login_required
def modifier_consultation(request, id):
    consultation = get_object_or_404(Consultation, id=id)

    if request.method == "POST":
        def parse_decimal(value):
            """Convertit une valeur texte en Decimal ou None si vide/incorrect."""
            if value and value.strip():
                try:
                    return Decimal(value.strip())
                except InvalidOperation:
                    return None
            return None

        # 🔹 Champs texte
        consultation.motif = request.POST.get("motif") or consultation.motif
        consultation.diagnostic = request.POST.get("diagnostic") or consultation.diagnostic
        consultation.statue = request.POST.get("statue") or consultation.statue
        consultation.issue_consultation = request.POST.get("issue_consultation") or consultation.issue_consultation
        consultation.constat_consultation = request.POST.get(
            "constat_consultation") or consultation.constat_consultation
        consultation.examen_demande = request.POST.get("examen_demande") or consultation.examen_demande
        consultation.traitement = request.POST.get("traitement") or consultation.traitement
        consultation.resultat_examen = request.POST.get("resultat_examen") or consultation.resultat_examen

        # 🔹 Champs numériques
        poids = parse_decimal(request.POST.get("poids"))
        taille = parse_decimal(request.POST.get("taille"))
        pouls = parse_decimal(request.POST.get("pouls"))
        TA = parse_decimal(request.POST.get("TA"))

        if poids is not None:
            consultation.poids = poids
        if taille is not None:
            consultation.taille = taille
        if pouls is not None:
            consultation.pouls = pouls
        if TA is not None:
            consultation.TA = TA

        # 🔹 Calcul automatique de l’IMC si poids et taille disponibles
        if consultation.poids is not None and consultation.taille is not None and consultation.taille > 0:
            consultation.IMC = round(consultation.poids / (consultation.taille * consultation.taille), 2)
        else:
            # Si IMC existait déjà, on garde sa valeur pour éviter le NULL
            consultation.IMC = consultation.IMC or Decimal('0.0')

        consultation.save()
        messages.success(request, "✅ Consultation mise à jour avec succès.")
        return redirect('Utilisateur:consultation')

    return redirect('Utilisateur:consultation')


@login_required(login_url='Utilisateur:Connexion')
def modifier_profil(request):
    user = request.user

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        prenom = request.POST.get("prenom", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not (nom and prenom and username):
            messages.error(request, "Nom, prénom et email sont obligatoires.")
            return redirect('Utilisateur:parametre')

        # Vérifier l'unicité de l'email si modifié
        if username != user.username and Utilisateur.objects.filter(username=username).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect('Utilisateur:parametre')

        user.nom = nom
        user.prenom = prenom
        user.username = username

        if password:
            user.set_password(password)

        user.save()
        messages.success(request, "Profil mis à jour avec succès !")
        return redirect('Utilisateur:parametre')

    return render(request, 'parametre/index.html', {"user": user})


@login_required(login_url='Utilisateur:Connexion')
def modifier_utilisateur(request, id):
    """
    Modifie un utilisateur existant.
    L'URL doit fournir l'id : path('modifier_utilisateur/<int:id>/', ...)
    """
    user = get_object_or_404(Utilisateur, id=id)

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Méthode non autorisée."}, status=405)

    # Récupération champs
    nom = request.POST.get("nom", "").strip()
    prenom = request.POST.get("prenom", "").strip()
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "").strip()  # facultatif : si vide => on ne change pas
    role_designation = request.POST.get("role", "").strip()
    service_id = request.POST.get("services", "").strip()  # ton <select name="services"> renvoie l'id du service

    # validation minimale
    if not (nom and prenom and username):
        return JsonResponse({"success": False, "message": "Nom, prénom et mail sont requis."}, status=400)

    # vérifier unicité username (sauf si c'est le même utilisateur)
    if Utilisateur.objects.exclude(id=user.id).filter(username=username).exists():
        return JsonResponse({"success": False, "message": "Ce mail/nom d'utilisateur est déjà utilisé."}, status=400)

    # appliquer mises à jour
    user.nom = nom
    user.prenom = prenom
    user.username = username

    if password:
        user.set_password(password)  # utilisation de set_password pour hasher correctement

    # Traitement service + rôle
    if service_id:
        try:
            service = Service.objects.get(id=int(service_id))
        except (Service.DoesNotExist, ValueError):
            return JsonResponse({"success": False, "message": "Service invalide."}, status=400)

        # On essaye de récupérer un rôle existant pour (designation, service)
        role_obj = None
        if role_designation:
            role_obj = Role.objects.filter(designation__iexact=role_designation, service=service).first()

        # Si pas trouvé -> on crée (optionnel, selon ta logique métier)
        if not role_obj and role_designation:
            role_obj = Role.objects.create(designation=role_designation, service=service)

        if role_obj:
            user.role = role_obj

    elif role_designation:
        # cas où rôle fourni mais pas de service choisi : on recherche un rôle portant cette designation
        role_obj = Role.objects.filter(designation__iexact=role_designation).first()
        if role_obj:
            user.role = role_obj
        else:
            # si tu veux empêcher la création sans service, renvoie une erreur :
            return JsonResponse({"success": False, "message": "Choisir le service associé au rôle."}, status=400)

    user.save()

    # répondre différemment si requête AJAX (fetch)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "message": "Utilisateur modifié avec succès."})

    messages.success(request, "Utilisateur modifié avec succès.")
    return redirect('Utilisateur:gestion_utilisateur')


@login_required
def supprimer_consultation(request, id):
    consultations = get_object_or_404(Consultation, id=id)
    consultations.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, "Consultation supprimée avec succès.")
    return redirect('Utilisateur:consultation')


@login_required(login_url='Utilisateur:Connexion')
def supprimer_user(request, id):
    user = get_object_or_404(Utilisateur, id=id)
    user.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, "Utilisateur supprimé avec succès.")
    return redirect('Utilisateur:gestion_utilisateur')


@login_required(login_url='Utilisateur:Connexion')
def gestion_utilisateur(request):
    services = Service.objects.all()
    roles = Role.objects.all()
    utilisateur = Utilisateur.objects.select_related('role__service').all()
    utilisateurs = utilisateur.exclude(id=request.user.id).exclude(username="SuperUser")

    utilisateurs_aadmin = utilisateurs.filter(role__designation="ADMIN").count()
    utilisateurs_medecin = utilisateurs.filter(role__designation="MEDECIN").count()
    utilisateurs_total = utilisateurs.count()

    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    utilisateurs_actifs_auj = utilisateurs.filter(last_activity__gte=today_start).count()

    return render(request, 'utilisateurs/index.html', {
        'services': services,
        'roles': roles,
        'utilisateurs_total': utilisateurs_total,
        'utilisateurs_aadmin': utilisateurs_aadmin,
        'utilisateurs_medecin': utilisateurs_medecin,
        'utilisateurs_actifs_auj': utilisateurs_actifs_auj,
        'utilisateurs': utilisateurs
    })


def export_utilisateurs_pdf(request):
    utilisateurs = Utilisateur.objects.all()

    html_string = render_to_string('export_utilisateurs.html', {
        'utilisateurs': utilisateurs,
        'date_export': timezone.now(),
    })

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    return response


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


@csrf_exempt
def modifier_Rdvs(request, id):
    if request.method == "POST":
        rdv = get_object_or_404(RendezVous, id=id)
        rdv.motif = request.POST.get('motif')
        service_id = request.POST.get('service')  # maintenant ce sera un ID
        if service_id:
            rdv.service_id = int(service_id)
        rdv.date = request.POST.get('date')
        rdv.save()
        return JsonResponse({"success": "Rendez-vous mis à jour"})
    return JsonResponse({"error": "Méthode non autorisée"})


@csrf_exempt
def supprimer_Rdvs(request, id):
    if request.method == "POST":
        rdv = get_object_or_404(RendezVous, id=id)
        rdv.delete()
        return JsonResponse({"success": "Rendez-vous supprimé"})
    return JsonResponse({"error": "Méthode non autorisée"})


@csrf_exempt
def modifier_patient(request):
    if request.method == "POST":
        id = request.POST.get("patient_id")
        patient = get_object_or_404(Patient, id=id)
        patient.nom = request.POST.get("nom")
        patient.prenom = request.POST.get("prenom")
        patient.age = request.POST.get("age")
        patient.numero = request.POST.get("numero")
        patient.nationalite = request.POST.get("nationalite")
        patient.groupe_sanguin = request.POST.get("groupe_sanguin")
        patient.save()
        return JsonResponse({"success": "Patient mis à jour avec succès"})
    return JsonResponse({"error": "Méthode invalide"})


@csrf_exempt  # nécessaire si on utilise fetch POST avec CSRF manuel
def supprimer_patient(request, id):
    if request.method == "POST":  # on accepte POST maintenant
        patient = get_object_or_404(Patient, id=id)
        patient.delete()
        return JsonResponse({"success": "Patient supprimé avec succès"})
    return JsonResponse({"error": "Méthode non autorisée"})


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
def ajouter_utilisateur(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                nom = request.POST.get('nom', '').strip()
                prenom = request.POST.get('prenom', '').strip()
                username = request.POST.get('username', '').strip()
                password = request.POST.get('password', '').strip()
                role_designation = request.POST.get('role', '').strip()
                service_id = request.POST.get('services', '').strip()

                # Vérification des champs requis
                if not (nom and prenom and username and password and role_designation and service_id):
                    return JsonResponse({'error': 'Veuillez remplir tous les champs requis.'}, status=400)

                # Vérifier si le nom d’utilisateur existe déjà
                if Utilisateur.objects.filter(username=username).exists():
                    return JsonResponse({'error': 'Ce nom d’utilisateur existe déjà.'}, status=400)

                # Récupérer le service sélectionné
                service = Service.objects.get(id=service_id)

                # Vérifier si le rôle existe déjà pour ce service, sinon le créer
                role, created = Role.objects.get_or_create(
                    designation=role_designation,
                    service=service
                )

                # Créer l'utilisateur
                utilisateur = Utilisateur.objects.create(
                    nom=nom,
                    prenom=prenom,
                    username=username,
                    role=role,
                    last_activity=timezone.now(),
                )
                utilisateur.set_password(password)
                utilisateur.save()

            return JsonResponse({'success': 'Utilisateur ajouté avec succès !'})

        except Service.DoesNotExist:
            return JsonResponse({'error': 'Service invalide.'}, status=400)
        except Exception as e:
            print("Erreur:", e)
            return JsonResponse({'error': 'Erreur lors de l’ajout de l’utilisateur.'}, status=400)

    return JsonResponse({'error': 'Requête invalide.'}, status=400)


@login_required(login_url='Utilisateur:Connexion')
def gestionRdvs(request):
    user_connect = request.user
    user_role = user_connect.role.designation
    services = Service.objects.all()
    patients = Patient.objects.all()

    # Date et heure actuelles
    maintenant = timezone.now()

    # 1. Récupération initiale des rendez-vous selon le rôle
    if user_role == "CAISSE":
        queryset = RendezVous.objects.all()
    elif user_role == "MEDECIN":
        service_medecin = user_connect.role.service
        queryset = RendezVous.objects.filter(service=service_medecin)
    elif user_role == "ADMIN":
        queryset = RendezVous.objects.all()
    else:
        queryset = RendezVous.objects.none()

    # 2. Logique de tri complexe en SQL (Les à-venir en haut, les passés en bas)
    # On ajoute un champ temporaire 'est_depasse' (True si la date du rdv < maintenant)
    rendez_vous = queryset.annotate(
        est_depasse=Case(
            When(date__lt=maintenant, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    ).order_by(
        'est_depasse',  # False (à venir) apparaîtra en premier, True (passés) apparaîtra en bas
        'date'  # Les rendez-vous à venir seront triés du plus proche au plus lointain
    )

    patients_data = list(patients.values('code_patient', 'nom'))

    context = {
        'rendez_vous': rendez_vous,
        'rdv_maintenant': maintenant,
        'patients': patients,
        'services': services,
        'patients_json': json.dumps(patients_data, cls=DjangoJSONEncoder)
    }

    return render(request, 'rdv/index.html', context)


@login_required(login_url='Utilisateur:Connexion')
def hospitalisation(request):
    # Annoter chaque hospitalisation : 0 si pas de sortie, 1 si sortie
    hospitalisations = Hospitalisation.objects.select_related('patient').prefetch_related('sortie').annotate(
        has_sortie=Case(
            When(sortie__isnull=True, then=Value(0)),  # pas de sortie
            default=Value(1),  # sortie existante
            output_field=IntegerField()
        )
    ).order_by('has_sortie', 'id')  # Affiche d'abord les 0 (sans sortie), puis les 1 (avec sortie)

    patients = Patient.objects.all()

    return render(request, 'hospitalisation/index.html', {
        'hospitalisations': hospitalisations,
        'patients': patients
    })


@login_required(login_url='Utilisateur:Connexion')
def sorties(request):
    sorties = Sortie.objects.select_related("hospitalisation__patient").all()
    return render(request, 'sorties/index.html', {
        'sorties': sorties
    })


@login_required(login_url='Utilisateur:Connexion')
def consultation(request):
    consultations = Consultation.objects.all().select_related('patient', 'service').order_by('-id')
    patients = Patient.objects.all()
    services = Service.objects.all()

    consultations_details = []
    for consult in consultations:
        ordonnances = consult.ordonnances.all()  # multiple ordonnances
        arrets = consult.arrets.all()  # multiple arrêts
        recu = consult.recus.first()  # related_name="recus"
        prestations = recu.bulletins.all() if recu else []

        consultations_details.append({
            'id': consult.id,
            'patient': f"{consult.patient.nom} {consult.patient.prenom}",
            'service': consult.service.designation,
            'motif': consult.motif,
            'poids': consult.poids,
            'taille': consult.taille,
            'IMC': consult.IMC,
            'pouls': consult.pouls,
            'TA': consult.TA,
            'diagnostic': consult.diagnostic,
            'constat_consultation': consult.constat_consultation,
            'examen_demande': consult.examen_demande,
            'traitement': consult.traitement,
            'issue_consultation': consult.issue_consultation,
            'resultat_examen': consult.resultat_examen,
            'statue': consult.statue,
            'date': consult.date,
            'ordonnances': ordonnances,
            'arrets': arrets,
            'recu': recu,
            'prestations': prestations,
        })

    return render(request, 'consultation/index.html', {
        'consultations_details': consultations_details,
        'patients': patients,
        'services': services
    })


def pdf_consultation(request, consultation_id):
    consultation = get_object_or_404(
        Consultation.objects.select_related('patient', 'service'),
        id=consultation_id
    )
    ordonnances = consultation.ordonnances.all()
    arrets = consultation.arrets.all()
    recu = consultation.recus.first()
    prestations = recu.bulletins.all() if recu else []

    # Récupérer les antécédents du patient
    antecedents = consultation.patient.antecedents.first()  # si plusieurs, prends le premier
    ant_med = antecedents.ant_med if antecedents else ""
    ant_chirur = antecedents.ant_chirur if antecedents else ""
    ant_mal = antecedents.ant_mal if antecedents else ""
    for arret in arrets:
        arret.date_fin = arret.date_debut + timedelta(days=arret.nombre_jours)
    context = {
        'consultation': consultation,
        'ordonnances': ordonnances,
        'arrets': arrets,
        'recu': recu,
        'prestations': prestations,
        'ant_med': ant_med,
        'ant_chirur': ant_chirur,
        'ant_mal': ant_mal,
    }

    html_string = render_to_string("pdf_template.html", context)

    # Générer le PDF avec WeasyPrint
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf = temp_file.read()
    finally:
        temp_file.close()
        os.unlink(temp_file.name)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Consultation_{uuid.uuid4().hex}.pdf"'
    return response


def recu_sortie(request, sortie_id):
    sortie = get_object_or_404(Sortie.objects.select_related('hospitalisation__patient'), id=sortie_id)
    context = {"sortie": sortie, "hospitalisation": sortie.hospitalisation, "patient": sortie.hospitalisation.patient}

    html_string = render_to_string("recu_sortie.html", context)

    # Générer PDF avec WeasyPrint
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf = temp_file.read()
    finally:
        temp_file.close()
        os.unlink(temp_file.name)  # suppression du fichier

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename = f"Recu_{sortie.id}_{uuid.uuid4().hex}.pdf"'
    return response

def carte_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    context = {
        "patient": patient,
    }

    html_string = render_to_string("carte_patient.html", context)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf = temp_file.read()
    finally:
        temp_file.close()
        os.unlink(temp_file.name)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Carte_Patient_{patient.code_patient}_{uuid.uuid4().hex}.pdf"'
    return response

@login_required(login_url='Utilisateur:Connexion')
def enregistrer_sortie(request, hosp_id):
    hospitalisation = get_object_or_404(Hospitalisation, id=hosp_id)

    if request.method == "POST":
        montant_total = request.POST.get("montant_total", 0)
        observation = request.POST.get("observation", "")

        with transaction.atomic():
            # Création du reçu
            recu = Recu.objects.create(
                montant=montant_total,
                total=montant_total,
                monnaie=0,
                details=f"Sortie après hospitalisation - {hospitalisation.patient.nom}"
            )

            # Création de la sortie
            sortie = Sortie.objects.create(
                hospitalisation=hospitalisation,
                montant_total=montant_total,
                observation=observation,
                recu=recu
            )

        return redirect("Utilisateur:hospitalisation")


@login_required(login_url='Utilisateur:Connexion')
def examens(request):
    examens = Examen.objects.select_related("patient").all()
    patients = Patient.objects.all()
    return render(request, "examens/index.html", {
        "examens": examens,
        "patients": patients
    })


@login_required(login_url='Utilisateur:Connexion')
def ajouter_examen(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                code_patient = request.POST.get("code_patient", "").strip()
                patient = get_object_or_404(Patient, code_patient=code_patient)

                type_examen = request.POST.get("type_examen", "").strip()
                service_id = request.POST.get("service", "").strip()
                service = get_object_or_404(Service, id=service_id) if service_id else None

                examen = Examen.objects.create(
                    patient=patient,
                    service=service,
                    type_examen=type_examen,
                    resultat=request.POST.get("resultat", "").strip()
                )

            return JsonResponse({"success": "Examen enregistrés avec succès !"})

        except Exception as e:
            print("Erreur:", e)
            return JsonResponse({"error": "Erreur lors de l'enregistrement."}, status=400)

    return JsonResponse({"error": "Requête invalide."}, status=400)


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
    patients = Patient.objects.all()

    if request.method == "POST":
        try:
            with transaction.atomic():
                patient = get_object_or_404(Patient, code_patient=request.POST.get('code_patient', '').strip())
                ant_med = request.POST.get('ant_med', '').strip()
                ant_mal = request.POST.get('ant_mal', '').strip()
                ant_chirur = request.POST.get('ant_chirur', '').strip()
                if ant_med or ant_mal or ant_chirur:
                    Antecedent.objects.create(
                        patient=patient,
                        ant_med=ant_med,
                        ant_mal=ant_mal,
                        ant_chirur=ant_chirur
                    )

                def parse_decimal(value):
                    if value and value.strip():
                        try:
                            return Decimal(value.strip())
                        except InvalidOperation:
                            return Decimal('0.0')
                    return Decimal('0.0')

                poids = parse_decimal(request.POST.get('poids'))
                taille = parse_decimal(request.POST.get('taille'))
                pouls = parse_decimal(request.POST.get('pouls'))
                TA = parse_decimal(request.POST.get('TA'))
                IMC = Decimal('0.0')
                if poids > 0 and taille > 0:
                    IMC = round(poids / (taille * taille), 2)

                consultation = Consultation.objects.create(
                    patient=patient,
                    service=request.user.role.service,
                    motif=request.POST.get('motif', '').strip(),
                    poids=poids,
                    taille=taille,
                    IMC=IMC,
                    pouls=pouls,
                    TA=TA,
                    diagnostic=request.POST.get('diagnostic', '').strip(),
                    constat_consultation=request.POST.get('constat_consultation', '').strip(),
                    examen_demande=request.POST.get('examen_demande', '').strip(),
                    traitement=request.POST.get('traitement', '').strip(),
                    issue_consultation=request.POST.get('issue_consultation', '').strip(),
                    resultat_examen=request.POST.get('resultat_examen', '').strip(),
                    statue=request.POST.get('statue', '').strip()
                )

                # Ordonnance
                contenu_ord = request.POST.get('contenu_ordonnance', '').strip()
                if contenu_ord:
                    Ordonnance.objects.create(consultation=consultation, contenu=contenu_ord)

                # Arret
                nombre_jours = request.POST.get('nombre_jours', '').strip()
                date_str = request.POST.get('date_debut', '').strip()
                if nombre_jours and date_str:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    date_aware = timezone.make_aware(date_obj)
                    ArretTravail.objects.create(
                        consultation=consultation,
                        nombre_jours=int(nombre_jours),
                        date_debut=date_aware,
                        nom_med=f"{request.user.nom} {request.user.prenom}"
                    )

                # Recu
                designation_prestation = request.POST.get('designation_prestation', '').strip()
                prix_prestation = request.POST.get('prix_prestation', '').strip()
                if designation_prestation and prix_prestation:
                    prix_val = float(prix_prestation)
                    recu = Recu.objects.create(
                        consultation=consultation,
                        montant=prix_val,
                        total=prix_val,
                        monnaie=0,
                        details=designation_prestation
                    )
                    Prestation.objects.create(
                        recu=recu,
                        designation=designation_prestation,
                        prix=prix_val
                    )

                return JsonResponse({'success': 'Consultation enregistrée avec succès !'})

        except Exception as e:
            return JsonResponse({'error': str(e)})

    # GET
    return render(request, 'consultation/index.html', {'patients': patients})


@login_required(login_url='Utilisateur:Connexion')
def ajouter_Rdvs(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                code_patient = request.POST.get('code_patient', '').strip()
                patient = get_object_or_404(Patient, code_patient=code_patient)
                if request.user.role.designation == "MEDECIN":
                    service_id = request.user.role.service.designation
                else:
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
