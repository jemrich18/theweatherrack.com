from django import forms
from .models import HuntingArea

class HuntingAreaForm(forms.ModelForm):
    location_search = forms.CharField(
        max_length=200,
        required=True,
        label='Location',
        help_text='Enter a city, county, or address'
    )

    class Meta:
        model = HuntingArea
        fields = ['name', 'location_search']