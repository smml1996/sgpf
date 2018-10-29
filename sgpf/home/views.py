from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse,Http404,HttpResponseRedirect
from .models import Concept
from django.contrib.auth.models import User
from .models import Concept, DailyInput
from .forms import ConfigurationForm, DailyInputForm, ChangePercentageForm
import json
from datetime import datetime as dt
from django.contrib.auth import views as auth_views
from login.models import Savings,Savings_Percentage
from django.core import serializers
from django.db import connection
from django.core.serializers.json import DjangoJSONEncoder
import calendar
from django.db.models import Sum
from decimal import Decimal
from django.contrib.auth.decorators import login_required

# Create your views here.


def getNumberOfDays(date):
    #this functions gives the numbers of days a month has
    return calendar.monthrange(date.year, date.month)[1]

def checkIfSavingExist(user, year, month):
    #function to see if we need to create a new saving register for this month
    saving = Savings.objects.filter(year=year, month=month, user=user)
    if len(saving) == 0:
        saving = Savings(year=year, month =month, user=user)
        previousSaving = Savings.objects.filter(user=user, year__lte=year).order_by('-month')
        if(len(previousSaving) > 0):
            saving.value = previousSaving[0].value
            saving.save()

def DeleteDailyInput(request):
    #begin variables:
    id_concept = int(request.GET['id_concept'])
    date = dt.strptime(str(request.GET['date']), "%d/%m/%Y") #daily input date
    daily = DailyInput.objects.filter(id=id_concept, date_from__gte =date)
    user = request.user.id
    #end variables
    if len(daily) > 0:
        daily = daily[0]
        if daily.type == False: #if is an income
            if daily.period == 0: # if it has no period
                saving = Savings.objects.get(user=user, month= daily.date_from.month, year=daily.date_from.year)
                saving.value-= daily.savings_value
                saving.save()
            else:
                #getting old savings in which months are different from now().month
                saving = Savings.objects.filter(user=user, month__gte = daily.date_from.month, year__gte = daily.date_from.year, month__lt=dt.now().month)
                for s in saving:
                    s.value -=  daily.savings_value
                    s.save()
        daily.delete()
    data ={} # use empty json as response meaning end of processing
    return HttpResponse(json.dumps(data), content_type="application/json")

def changeSavingsPercentage(request):
    user = User.objects.get(id=request.user.id)
    currentPercentage=0
    sp = Savings_Percentage.objects.get(user=user)
    if request.method == 'POST':
        form  = ChangePercentageForm(request.POST)
        if form.is_valid():

            sp.percentage = Decimal(form.cleaned_data['value'])/100
            currentPercentage = sp.percentage
            sp.save()
    else:
        currentPercentage = sp.percentage
    form = ChangePercentageForm()
    context ={'currentPercentage':currentPercentage*100, 'form':form} # use empty json as response meaning end of processing
    template = loader.get_template('change_percentage.html')
    return HttpResponse(template.render(context, request))


def getConcepts(usuario):
    # get only concepts which are not disabled by user
    conceptos = Concept.objects.filter(user=usuario, is_disabled=False)
    return conceptos


def getCurrentSaving(user, month=dt.now().month, year=dt.now().year , d=dt.now().day):
    #used to calculate savings showed in home

    checkIfSavingExist(user, year, month)
    now = dt(year=year, month=month, day=d)

    currentSaving = Savings.objects.get(user=user, year=year, month=month).value #this gives the savings that has no period por this year's month

    #begin calculate daily savings
    try:
        currentSaving+= (DailyInput.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=1).aggregate(suma=Sum('savings_value'))['suma'] or 0)*d
    except Exception as e:
        print("exception ocurred")
    #end calculate daily savings

    #begin calculate monthly savings
    currentSaving+= DailyInput.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=3).aggregate(suma=Sum('savings_value'))['suma'] or 0
    #end begin monthly savings

    #begin calculate monthly
    if getNumberOfDays(now) == d:
        currentSaving+= DailyInput.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=3).aggregate(suma=Sum('savings_value'))['suma'] or 0
        # if day is last day of month, then sum biweekly incomes too:
        currentSaving+=( DailyInput.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=2).aggregate(suma=Sum('savings_value'))['suma'] or 0)*2
    #end begin monthly savings

    #check if half month is passed:
    elif d >=14:
        currentSaving+= DailyInput.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=2).aggregate(suma=Sum('savings_value'))['suma'] or 0
    return currentSaving


def updatePast(user):
    now = dt.now()
    savingsPast = Savings.objects.filter(user=user, month__lt = now.month, year__lte = now.year, isFinalValue=False)

    for saving in savingsPast:
        #for each saving of each month we want to know if that month has passed and we get to know
        #how much the user has saved
        saving.value = getCurrentSaving(user, saving.month, saving.year, calendar.monthrange(saving.year, saving.month)[1])
        saving.isFinalValue = True
        saving.save()


def getIncomeOrExpense(isExp, user, useMonth = False):
    now = dt.now()
    dailiesValue = Decimal(0.00)
    # getting all dailies of specific type (expense or income)
    dailes = DailyInput.objects.filter(user=user, date_from__lte=dt.now(),concept__type=isExp)

    #getting values for this daily input types with no period
    if not useMonth:
        dailiesValue += Decimal(dailes.filter(concept__period=0, date_from__gte= dt(year=dt.now().year, day=1, month=dt.now().month)).aggregate(suma=Sum('value'))['suma'] or 0.00)
    else:
        dailiesValue += Decimal(dailes.filter(concept__period=0, date_from__gte= dt(year=dt.now().year, month=1, day=1)).aggregate(suma=Sum('value'))['suma'] or 0.00)

    #getting daily dailyInputs for this type
    dailiesValue = Decimal(dailiesValue)
    if useMonth:
        dailiesValue +=Decimal(( dailes.filter(concept__period=1).aggregate(suma=Sum('value'))['suma'] or 0.00) * dt.now().day)
    else:
        day_of_year = (dt.now() - dt(dt.now().year, 1, 1)).days + 1
        dailiesValue +=Decimal( dailes.filter(concept__period=1).aggregate(suma=Sum('value'))['suma'] or Decimal(0)) * Decimal(day_of_year)

    #getting biweeklies
    multiplier = 0.00
    dailiesValue = Decimal(dailiesValue)
    if not useMonth:
        multiplier = dt.now().month *2 # we have the number of months * 2 biweekly incomes
    else:
        multiplier = 2
    if dt.now().day != getNumberOfDays(now):
        #if is not last day of month we have one less biweekly
        multiplier-=1
    if dt.now().day < 14:
        #if is not yet half month we dont have this biweekly neither
        multiplier-=1

    #multiplier = Decimal(multiplier)
    dailiesValue += Decimal((dailes.filter(concept__period=2).aggregate(suma=Sum('value'))['suma'] or 0.00) * multiplier)


    #getting monthlies
    if useMonth:
        multiplier = 1
    else:
        multiplier = dt.now().month

    if dt.now().day != getNumberOfDays(now):
        multiplier-=1
    #multiplier = Decimal(mutiplier)
    dailiesValue += Decimal((dailes.filter(concept__period=3).aggregate(suma=Sum('value'))['suma'] or 0.00) * multiplier)

    return dailiesValue


def getSummaryYear(user):
    incomes = getIncomeOrExpense(False, user)
    expenses = getIncomeOrExpense(True, user)
    return incomes - expenses


def getSummaryMonth(user):
    incomes = getIncomeOrExpense(False, user, True)
    expenses = getIncomeOrExpense(True, user, True)
    return incomes - expenses


def home(request):
    number = 1 # variable sent to interface, used to highlight home tab in navbar
    template = loader.get_template('home.html')

    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        summaryYear = getSummaryYear(user)
        summaryMonth = getSummaryMonth(user)
        todayDate = dt.today().strftime('%d/%m/%Y')
        currentSaving = getCurrentSaving(user)
        updatePast(user)
        context = {'number':number,'currentSaving':currentSaving,
                    'todayDate': todayDate, 'summaryYear':summaryYear,
                    'summaryMonth':summaryMonth }
        return HttpResponse(template.render(context, request))
    else:
        # if user not authenticated send her/him to login page
        return redirect('login/')


def SaveConcept(request):
    number= 3 # variable sent to interface, used to highlight home tab in navbar
    current_user = User.objects.get(id=request.user.id)
    form = ConfigurationForm()
    conceptos = getConcepts(current_user)
    template = loader.get_template('config.html')
    message = ""
    if request.method == "POST":
        form = ConfigurationForm(request.POST)
        # (save concept) case
        if form.is_valid():
            if(form.cleaned_data['isNewConcept'] == -1):
                message = "NEW CONCEPT CREATED"
                #begin variables:
                name = form.cleaned_data['name']
                value = form.cleaned_data['value']
                period = form.cleaned_data['period']
                type = form.cleaned_data['isExpense']
                #end variables
                newConcept = Concept(name = name, value = value, period = period, type=type, user= current_user)
                newConcept.save()
            else:
                message = "CONCEPT MODIFIED"
                concept = Concept.objects.filter(id_user=current_user, id=form.cleaned_data['isNewConcept'])[0]
                concept.name = form.cleaned_data['name']
                concept.value = form.cleaned_data['value']
                concept.period = form.cleaned_data['period']
                concept.type= form.cleaned_data['isExpense']
                concept.save()
        else:
            print(form.errors)
    context = {'number':number, 'conceptos': conceptos, 'form': form, 'message':message}
    return HttpResponse(template.render(context, request))


def disableConcept(request):
    # function used for ajax
    concept = Concept.objects.get(user__id =request.user.id, id= request.GET['id_concept'])
            # get concept of requsted user with specific id
            # delete first one
    concept.is_disabled = True
    concept.save()
    data = {} #send empty data as json, meaning end of processing
    return HttpResponse(json.dumps(data), content_type="application/json")


def AddDailyInput(request):
    current_user = User.objects.get(id=request.user.id)
    conceptos = getConcepts(current_user) # variable meant to be sent to interface
    number = 2 # variable sent to interface, used to highlight home tab in navbar
    isDailyInput = False # we dont have any message yet to show to user
    todayDate = dt.today().strftime('%d/%m/%Y')
            #default date to be displayed in this interface, is today's date

    message ="" #messages to display to user
    if request.method == 'POST':
        form  = DailyInputForm(request.POST)
        isDailyInput = True # we have some message to show to user
        if form.is_valid():
            message = "daily input added"
            # creating new dailyInput:  (Add daily input)

            #begin variables:
            value=form.cleaned_data['value']
            id_concept = form.cleaned_data['id_concepto']
            concept = Concept.objects.get(id=id_concept)
            from_date = form.cleaned_data['from_date']
            percentage = Savings_Percentage.objects.get(user=current_user).percentage
            savings_value = percentage*value
            #end variables
            dailyInput = DailyInput(user=current_user, concept=concept, value=value, date_from =from_date , savings_value=savings_value)

            checkIfSavingExist(current_user, dailyInput.date_from.month, dailyInput.date_from.year)

            if concept.period == 0 and concept.type == False:
                # if is a concept that has no period and is an income then sum to savings
                # for the refering month and year

                dailyMonth = dailyInput.date_from.month
                dailyYear = dailyInput.date_from.year

                saving = Savings.objects.filter(user= current_user, month=dailyMonth, year=dailyYear)[0]
                saving.value+=savings_value
                saving.save()

                dailyInput.value -= savings_value
            dailyInput.save()
        else:
            #form is not valid, dont have all data to create new daily input
            message = "couldn't save this daily input"

    form = DailyInputForm()
    template = loader.get_template('dailyInput.html')
    context = {'number':number, 'conceptos': conceptos, 'todayDate':todayDate,
                'isDailyInput': isDailyInput, 'form': form, 'message':message}
    return HttpResponse(template.render(context, request))


def visualize(request):
    type = request.GET['type']
    from_date = dt.strptime(str(request.GET['from']), "%d/%m/%Y")
    to_date = dt.strptime(str(request.GET['to']), "%d/%m/%Y")
    print(from_date.day)
    dailyUnique = ""
    dailyDaily = ""
    dailyBiweekly = ""
    dailyMonthly = ""
    current_user = User.objects.get(id=request.user.id)
    print(calendar.monthrange(from_date.year, from_date.month)[1])
    if type == '1':
        # we should load Incomes
        dailyUnique= DailyInput.objects.filter(user=current_user, concept__period=0, concept__type = False, date_from__gte = from_date, date_from__lte = to_date).order_by('-date_from')
        dailyDaily= DailyInput.objects.filter(user=current_user, concept__period=1, concept__type = False, date_from__lte = to_date).order_by('-date_from')
        if (from_date.day <=14 and to_date.day>=14 and to_date.month == from_date.month )or to_date.month > from_date.month:
            # check if there is some 14th of some month in this range
            dailyBiweekly= DailyInput.objects.filter(user=current_user, concept__period=2, concept__type = False, date_from__lte = to_date).order_by('-date_from')
        if(to_date.month>from_date.month):
            #check if there is some end of month in this range
            dailyMonthly= DailyInput.objects.filter(user=current_user, concept__period=3, concept__type = False, date_from__lte = to_date).order_by('-date_from')
    else:
        # we should load expenses
        dailyUnique= DailyInput.objects.filter(user=current_user, concept__period=0, concept__type =True, date_from__gte = from_date, date_from__lte = to_date).order_by('-date_from')
        dailyDaily= DailyInput.objects.filter(user=current_user, concept__period=1, concept__type =True, date_from__lte = to_date).order_by('-date_from')
        if (from_date.day <=14 and to_date.day>=14 and to_date.month == from_date.month ) or to_date.month > from_date.month:
            # check if there is some 14th of some month in this range
            dailyBiweekly= DailyInput.objects.filter(user=current_user, concept__period=2, concept__type =True, date_from__lte = to_date).order_by('-date_from')
        if(to_date.month>from_date.month):
            #check if there is some end of month in this range
            dailyMonthly= DailyInput.objects.filter(user=current_user, concept__period=3, concept__type =True, date_from__lte = to_date).order_by('-date_from')

    #begin serialization of each queryset
    json_dataUnique= serializers.serialize('json', dailyUnique, cls= DjangoJSONEncoder, use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    json_dataDaily = serializers.serialize('json', dailyDaily, cls= DjangoJSONEncoder,use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    json_dataBiweekly = serializers.serialize('json', dailyBiweekly, cls= DjangoJSONEncoder,use_natural_foreign_keys=True, fields=('date_from', 'value', 'concept'))
    json_dataMonthly = serializers.serialize('json', dailyMonthly, cls= DjangoJSONEncoder,use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    #end serialization of each queryset

    #put all together in a whole json
    json_data = {'unique':json_dataUnique,
                'daily': json_dataDaily,
                'biweek':json_dataBiweekly,
                'monthly':json_dataMonthly}

    #return json response
    return HttpResponse(json.dumps(json_data), content_type='application/json')

def simulateBalance(request):
    number = 4 # variable sent to interface, used to highlight home tab in navbar
    context ={ 'number':number}
    template = loader.get_template('simulator.html')
    return HttpResponse(template.render(context, request))

def visualizeIncomes(request):
    from_date = dt.strptime(str(request.GET['from']), "%d/%m/%Y")
    to_date = dt.strptime(str(request.GET['to']), "%d/%m/%Y")
    dailyUnique = ""
    dailyDaily = ""
    dailyBiweekly = ""
    dailyMonthly = ""
    current_user = User.objects.get(id=request.user.id)
    # we should load Incomes
    dailyUnique= DailyInput.objects.filter(user=current_user, concept__period=0, concept__type = False, date_from__gte = from_date, date_from__lte = to_date).order_by('-date_from')
    dailyDaily= DailyInput.objects.filter(user=current_user, concept__period=1, concept__type = False, date_from__lte = to_date).order_by('-date_from')

    if (from_date.day <=14 and to_date.day>=14 and to_date.month == from_date.month )or to_date.month > from_date.month:
        # check if there is some 14th of some month in this range
        dailyBiweekly= DailyInput.objects.filter(user=current_user, concept__period=2, concept__type = False, date_from__lte = to_date).order_by('-date_from')
    if(to_date.month>from_date.month):
        #check if there is some end of month in this range
        dailyMonthly= DailyInput.objects.filter(user=current_user, concept__period=3, concept__type = False, date_from__lte = to_date).order_by('-date_from')
    #begin serialization of each queryset
    json_dataUnique= serializers.serialize('json', dailyUnique, cls= DjangoJSONEncoder, use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    json_dataDaily = serializers.serialize('json', dailyDaily, cls= DjangoJSONEncoder,use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    json_dataBiweekly = serializers.serialize('json', dailyBiweekly, cls= DjangoJSONEncoder,use_natural_foreign_keys=True, fields=('date_from', 'value', 'concept'))
    json_dataMonthly = serializers.serialize('json', dailyMonthly, cls= DjangoJSONEncoder,use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    #end serialization of each queryset

    #put all together in a whole json
    json_data = {'unique':json_dataUnique,
                'daily': json_dataDaily,
                'biweek':json_dataBiweekly,
                'monthly':json_dataMonthly}

    #return json response
    return HttpResponse(json.dumps(json_data), content_type='application/json')


def visualizeExpenses(request):
    from_date = dt.strptime(str(request.GET['from']), "%d/%m/%Y")
    to_date = dt.strptime(str(request.GET['to']), "%d/%m/%Y")
    dailyUnique = ""
    dailyDaily = ""
    dailyBiweekly = ""
    dailyMonthly = ""
    current_user = User.objects.get(id=request.user.id)
    dailyUnique= DailyInput.objects.filter(user=current_user, concept__period=0, concept__type =True, date_from__gte = from_date, date_from__lte = to_date).order_by('-date_from')
    dailyDaily= DailyInput.objects.filter(user=current_user, concept__period=1, concept__type =True, date_from__lte = to_date).order_by('-date_from')
    if (from_date.day <=14 and to_date.day>=14 and to_date.month == from_date.month ) or to_date.month > from_date.month:
        # check if there is some 14th of some month in this range
        dailyBiweekly= DailyInput.objects.filter(user=current_user, concept__period=2, concept__type =True, date_from__lte = to_date).order_by('-date_from')
    if(to_date.month>from_date.month):
        #check if there is some end of month in this range
        dailyMonthly= DailyInput.objects.filter(user=current_user, concept__period=3, concept__type =True, date_from__lte = to_date).order_by('-date_from')

    #begin serialization of each queryset
    json_dataUnique= serializers.serialize('json', dailyUnique, cls= DjangoJSONEncoder, use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    json_dataDaily = serializers.serialize('json', dailyDaily, cls= DjangoJSONEncoder,use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    json_dataBiweekly = serializers.serialize('json', dailyBiweekly, cls= DjangoJSONEncoder,use_natural_foreign_keys=True, fields=('date_from', 'value', 'concept'))
    json_dataMonthly = serializers.serialize('json', dailyMonthly, cls= DjangoJSONEncoder,use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    #end serialization of each queryset

    #put all together in a whole json
    json_data = {'unique':json_dataUnique,
                'daily': json_dataDaily,
                'biweek':json_dataBiweekly,
                'monthly':json_dataMonthly}

    #return json response
    return HttpResponse(json.dumps(json_data), content_type='application/json')



def visualizeSavings(request):
    number = 5 # variable sent to interface, used to highlight home tab in navbar
    context = {'number':number}
    template = loader.get_template('savings.html')
    return HttpResponse(template.render(context, request))
