from django.contrib.auth.forms import AuthenticationForm


class ConnexionForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(ConnexionForm, self).__init__(*args, **kwargs)
        self.fields['username'].error_messages = {
            'required': "Nom d'utilisateur invalide !"
        }
        self.fields['password'].error_messages = {
            'required': "Mot de passe invalide!"
        }
        self.error_messages.update({
            "invalid_login": "ce compte n'existe pas",
            "inactive": "Ce compte est inactif. Veuillez contacter l'administrateur.",
        })