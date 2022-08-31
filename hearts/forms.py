from django import forms


class NewPlayerForm(forms.Form):
    """
    Form to submit when creating a new player.

    We really only care about getting the user's name. In the future this could
    be an actual login.
    """

    # Name to attach to the user starting the game.
    name = forms.CharField(label='Name', max_length=100)
