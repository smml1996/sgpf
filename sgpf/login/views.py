from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse,Http404,HttpResponseRedirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .models import Savings_Percentage, Savings


from login.forms import SignUpForm
from datetime import datetime


# Create your views here.
def isEmailValid(email):
    #funcion para saber si un email esta en uso
        # si esta en uso retornar falso
    users = User.objects.all()
    temp = users.filter(email=email) # get all users with specific email
    return len(temp) == 0 # si la longitud del <queryset> es 0 entonce el email no esta en uso

def signup(request):
    message = "" # help messages for user
    if request.method == 'POST':
        form = SignUpForm(request.POST) # get form filled by user
        if form.is_valid(): # django validations
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            email = form.cleaned_data.get('email')
            if isEmailValid(email): #verify this email is not already in use
                form.save() # save new user
                newUser = User.objects.filter(username = username, email = email)[0]

                sp = Savings_Percentage(user = newUser)
                sp.save() #create new register for this new user regarding her/his desired saving amount

                #saving = Savings(user = newUser, month=datetime.now().month, year=datetime.now().year)
                #saving.save() # create new register for new user in which we will know how much is she/he saving

                return redirect('../login/')
            else:
                message = "not valid email"
        else:
            print("form not valid")
            message = form.errors # gather error messages to show to user
    form = SignUpForm()
    return render(request, 'registration/signup.html',{'form': form, 'message': message})
