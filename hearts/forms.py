from django import forms


class NewGameForm(forms.Form):
    """
    Form to submit when creating a new game.

    We really only care about getting the user's name and once we add some
    kind of client-side persistence then we won't even need this.

    We should consider adding a difficulty option if we can (easy/medium/hard).
    """

    # Name to attach to the user starting the game.
    name = forms.CharField(label='Name', max_length=100)
