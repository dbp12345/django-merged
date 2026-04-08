from django import forms

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["notebook", "title", "content"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Note title",
                    "autocomplete": "off",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "rows": 18,
                    "placeholder": "Write here...",
                }
            ),
        }

