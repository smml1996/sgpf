from django import forms

from .models import Concept

class Configuration_Form(forms.Form):
    # form inputs for conf.html
    is_new_concept = forms.IntegerField()
    name = forms.CharField(max_length=25)
    value = forms.DecimalField(decimal_places=2)
    period = forms.ChoiceField(choices=(
        (0, 'No Period'),
        (1, 'Daily'),
        (2, 'Biweekly'),
        (3, 'Monthly')
    ))

    is_expense = forms.ChoiceField(choices=(
        (True, 'Expense'),
        (False, 'Income'),
    ))

class Change_Percentage_Form(forms.Form):
    value = forms.DecimalField(decimal_places=2)

class Simulate_Balance_Form(forms.Form):
    value = forms.DecimalField(decimal_places=2)
    period = forms.ChoiceField(choices=(
        (0, 'No Period'),
        (1, 'Daily'),
        (2, 'Biweekly'),
        (3, 'Monthly')
    ))

    is_expense = forms.ChoiceField(choices=(
        (True, 'Expense'),
        (False, 'Income'),
    ))
    from_date = forms.DateField(input_formats=['%d/%m/%Y'])


class Daily_Input_Form(forms.Form):
    # form inputs for Daily_Input.html
    id_concepto = forms.IntegerField()
    value = forms.DecimalField(decimal_places=2)
    from_date = forms.DateField(input_formats=['%d/%m/%Y'])
    is_use_savings = forms.ChoiceField( choices=(
        (False, 'No'),
        (True, 'Yes'),
    ))
