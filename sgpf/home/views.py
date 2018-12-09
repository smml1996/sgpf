from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse,Http404,HttpResponseRedirect
from .models import Concept
from django.contrib.auth.models import User
from home.models import Concept, Daily_Input
from .forms import Configuration_Form, Daily_Input_Form, Change_Percentage_Form
from .forms import Simulate_Balance_Form
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

def get_number_of_days(date):
    #this functions gives the numbers of days a month has
    return calendar.monthrange(date.year, date.month)[1]

def check_if_saving_exist(user, year, month):
    #function to see if we need to create a new saving register for this month

    saving = Savings.objects.filter(year=year, month=month, user=user)

    if len(saving) == 0:
        saving = Savings(year=year, month =month, user=user) # create saving if user don't have it for this month of the year
        previous_saving = Savings.objects.filter(user=user, year__lte=year).order_by('-month') # get last saving

        if(len(previous_saving) > 0):
            saving.value = previous_saving[0].value #initial value is the previos saving if it exists
        else:
            saving.value = 0 # if no previous saving, then it is 0
        saving.save()

def delete_daily_input(request):
    #use case: delete daily input
    #begin variables:
    concept = Concept.objects.get(id=int(request.GET['id_concept']))
    date = dt.strptime(str(request.GET['date']), "%d/%m/%Y") #daily input date
    daily = Daily_Input.objects.filter(concept=concept, date_from =date).values('concept__period', 'concept__type','savings_value','date_from','id', 'is_using_savings', 'value')
    user = request.user.id
    #end variables
    if len(daily) > 0:
        daily = daily[0]
        Daily_Input.objects.get(id=daily['id']).delete()
        if daily['concept__type'] == False: #if is an income
            if daily['concept__period'] == 0: # if it has no period
                saving = Savings.objects.get(user=user, month= daily.from_date.month, year=daily.from_date.year)
                saving.value-= daily.savings_value
                saving.save()
            else:
                #getting old savings in which months are different from now().month
                saving = Savings.objects.filter(user=user, month__gte = daily['date_from'].month, year__gte = daily['date_from'].year, month__lt=dt.now().month)
                for s in saving:
                    s.value -=  daily['savings_value']
                    s.save()
        elif daily['is_using_savings'] == True: # if is expense and she/he used savings s
            saving = Savings.objects.get(user=user, month= daily.from_date.month, year=daily.from_date.year)
            saving.value-= daily['value']

    data ={} # use empty json as response meaning end of processing
    return HttpResponse(json.dumps(data), content_type="application/json")

def change_savings_percentage(request):
    #use case: change savings percentage

    user = User.objects.get(id=request.user.id)
    current_percentage=0
    sp = Savings_Percentage.objects.get(user=user)
    if request.method == 'POST':
        form  = Change_Percentage_Form(request.POST)
        if form.is_valid():

            sp.percentage = Decimal(form.cleaned_data['value'])/100 # get normal form to save percentage as a number between 0 and 1 (inclusive)
            current_percentage = sp.percentage
            sp.save()
    else:
        current_percentage = sp.percentage
    form = Change_Percentage_Form()
    context ={'current_percentage':current_percentage*100, 'form':form} # use empty json as response meaning end of processing
    template = loader.get_template('change_percentage.html')

    return HttpResponse(template.render(context, request))


def get_concepts(usuario):
    # get only concepts which are not disabled by user
    conceptos = Concept.objects.filter(user=usuario, is_disabled=False)
    return conceptos


def get_current_saving(user, month=dt.now().month, year=dt.now().year , d=dt.now().day):
    #used to calculate savings showed in home

    check_if_saving_exist(user, year, month)
    now = dt(year=year, month=month, day=d)

    current_saving = Savings.objects.get(user=user, year=year, month=month).value #this gives the savings that has no period por this year's month

    #begin calculate daily savings
    current_saving+= (Daily_Input.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=1).aggregate(suma=Sum('savings_value'))['suma'] or 0)*d
    #end calculate daily savings

    #begin calculate monthly
    if get_number_of_days(now) == d:
        current_saving+= Daily_Input.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=3).aggregate(suma=Sum('savings_value'))['suma'] or 0
        # if day is last day of month, then sum biweekly incomes too:
        current_saving+=( Daily_Input.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=2).aggregate(suma=Sum('savings_value'))['suma'] or 0)*2
    #end begin monthly savings

    #check if half month is passed:
    elif d >=14:
        current_saving+= Daily_Input.objects.filter( user=user,date_from__lte = now,concept__type=False, concept__period=2).aggregate(suma=Sum('savings_value'))['suma'] or 0
    return current_saving



def update_past(user):

    now = dt.now()
    savingsPast = Savings.objects.filter(user=user, month__lt = now.month, year__lte = now.year, is_final_value=False)

    for saving in savingsPast:
        # for each saving of each month we want to know if that month has passed and we get to know
        # how much the user has saved
        saving.value = get_current_saving(user, saving.month, saving.year, calendar.monthrange(saving.year, saving.month)[1])
        saving.is_final_value = True
        saving.save()

def get_saldo_specific(user,is_expense):

        now = dt.now()
        dailies_value = Decimal(0.00)
        # getting all income dailies
        dailes = Daily_Input.objects.filter(user=user, date_from__lte=dt.now(),concept__type=is_expense)

        #getting values for this daily input types with no period
        dailies_value += Decimal(dailes.filter(concept__period=0, date_from__lte= now).aggregate(suma=Sum('value'))['suma'] or 0.00)
        #getting daily Daily_Inputs for this type
        dailies_value = Decimal(dailies_value)


        Daily_Inputs = dailes.filter(concept__period =1) # get daily inputs that have as period daily
        for di in Daily_Inputs:
            if di.date_from.year < now.year:
                day_of_year = (dt(month=12, day=31, year= di.date_from.year) - dt(di.year, 1, 1)).days + 1
                dailies_value +=Decimal(di.value) * Decimal(day_of_year)
            else:
                day_of_year = (dt.now() - dt(dt.now().year, 1, 1)).days + 1
                diference = day_of_year - ((dt(year=di.date_from.year, month=di.date_from.month, day=di.date_from.day ) - dt(di.date_from.year, 1, 1)).days + 1)
                dailies_value +=Decimal(di.value) * Decimal(diference)

        #getting biweeklies
        daily_biweek = dailes.filter(concept__period=2) # get daly inputs that has as period biweekly
        multiplier = 0.00
        for db in daily_biweek:
            if db.date_from.year < now.year:
                num_years = now.year - db.date_from.year -1
                num_middles = (12 - db.date_from.month)*2+1
                if(db.date_from.day<=14):
                    num_middles+=1
                multiplier = num_years*24 + num_middles
            else:
                num_middles = (12 - db.date_from.month)*2+1
                if(db.date_from.day<=14):
                    num_middles+=1
                multiplier = num_middles
            dailies_value +=Decimal(di.value) * Decimal(multiplier)


        daily_month = dailes.filter(concept__period=3) #get daily inputs that have as period monthly
        multiplier = 0.00
        for db in daily_month:
            if db.date_from.year < now.year:
                num_years = now.year - db.date_from.year -1
                num_middles = (12 - db.date_from.month)+1
                if(db.date_from.day<=14):
                    num_middles+=1
                multiplier = num_years*12 + num_middles
            else:
                num_middles = (12 - db.date_from.month)+1
                multiplier = num_middles
            dailies_value +=Decimal(di.value) * Decimal(multiplier)
            return dailies_value


def get_saldo(user):
    incomes  = get_saldo_specific(user, False)
    expenses= get_saldo_specific(user, True)
    return incomes - expenses

def can_expense(user, value, is_use_savings):
    #function to see if a user has money to expend

    if not is_use_savings:
        saldo = get_saldo(user)
        if saldo  >= value:
            return True
        return False

    actual_savings = Savings.objects.get(user=user, month= dt.now().month, year=dt.now().year)
    if actual_savings.value >=value:
        actual_savings.value-=value
        actual_savings.save()
        return True
    return False



def get_income_or_expense(is_exp, user, use_month = False):
    now = dt.now()
    dailies_value = Decimal(0.00)
    # getting all dailies of specific type (expense or income)

    dailes = Daily_Input.objects.filter(user=user, date_from__lte=dt.now(),concept__type=is_exp)


    #getting values for this daily input types with no period
    if not use_month:
        dailies_value += Decimal(dailes.filter(concept__period=0, date_from__gte= dt(year=dt.now().year, day=1, month=1)).aggregate(suma=Sum('value'))['suma'] or 0.00)
    else:
        dailies_value += Decimal(dailes.filter(concept__period=0, date_from__gte= dt(year=dt.now().year, day=1, month=dt.now().month)).aggregate(suma=Sum('value'))['suma'] or 0.00)

    #getting daily Daily_Inputs for this type
    dailies_value = Decimal(dailies_value)
    if use_month:
        dailies_value +=Decimal(( dailes.filter(concept__period=1).aggregate(suma=Sum('value'))['suma'] or 0.00) * dt.now().day)
    else:
        day_of_year = (dt.now() - dt(dt.now().year, 1, 1)).days + 1
        dailies_value +=Decimal( dailes.filter(concept__period=1,  date_from__lte=dt(year=dt.now().year, month=dt.now().month,day=dt.now().day)).aggregate(suma=Sum('value'))['suma'] or Decimal(0)) * Decimal(day_of_year)
        temp = dailes.filter(concept__period=1, date_from__gte= dt(year=dt.now().year, month=1, day=1))
        for d in temp:
            day_of_year_daily = ( (dt(year= d.date_from.year, month=d.date_from.month, day=d.date_from.day) - dt(d.date_from.year, 1, 1)).days )
            dailies_value+= Decimal(d.value * (day_of_year - day_of_year_daily))

    #getting biweeklies
    multiplier = 0.00
    dailies_value = Decimal(dailies_value)
    if not use_month:
        multiplier = dt.now().month *2 # we have the number of months * 2 biweekly incomes
    else:
        multiplier = 2
    if dt.now().day != get_number_of_days(now):
        #if is not last day of month we have one less biweekly
        multiplier-=1
    if dt.now().day < 14:
        #if is not yet half month we dont have this biweekly neither
        multiplier-=1

    #multiplier = Decimal(multiplier)
    if use_month:
        dailies_value += Decimal((dailes.filter(concept__period=2).aggregate(suma=Sum('value'))['suma'] or 0.00) * multiplier)
    else:
        dailies_value += Decimal((dailes.filter(concept__period=2, date_from__lte=dt(year=dt.now().year, month=dt.now().month,day=dt.now().day)).aggregate(suma=Sum('value'))['suma'] or 0.00) * multiplier)
        temp = dailes.filter(concept__period=2, date_from__gte=dt(year=dt.now().year, month=1,day=1))
        for d in temp:
            tempMultiplier = (d.date_from.month-1) *2
            if d.date_from.day >14:
                tempMultiplier-=1
            dailies_value+= Decimal(d.value * multiplier)
    #getting monthlies
    if use_month:
        multiplier = 1
    else:
        multiplier = dt.now().month

    if dt.now().day != get_number_of_days(now) or dt.now().day == 1:
        multiplier-=1
    #multiplier = Decimal(mutiplier)
    if use_month or True:
        dailies_value += Decimal((dailes.filter(concept__period=3).aggregate(suma=Sum('value'))['suma'] or 0.00) * multiplier)
    else:
        dailies_value += Decimal((dailes.filter(concept__period=3, date_from__lte=dt(year=dt.now().year, month=dt.now().month,day=dt.now().day)).aggregate(suma=Sum('value'))['suma'] or 0.00) * multiplier)
        temp = dailes.filter(concept__period=3, date_from__gte=dt(year=dt.now().year, month=1,day=1))
        for d in temp:
            tempMultiplier = multiplier - (d.date_from.month-1)
            dailies_value+=Decimal(d.value*tempMultiplier)


    return dailies_value


def get_summary_year(user):
    #function for summary box displayed in landing page
    incomes = get_income_or_expense(False, user)
    expenses = get_income_or_expense(True, user)
    return incomes - expenses


def get_summary_month(user):
    #function for summary box displayed in landing page
    incomes = get_income_or_expense(False, user, True)
    expenses = get_income_or_expense(True, user, True)
    return incomes - expenses


def home(request):
    number = 1 # variable sent to interface, used to highlight home tab in navbar
    template = loader.get_template('home.html')

    if request.user.is_authenticated:
        user = User.objects.get(id=request.user.id)
        summary_year = get_summary_year(user)

        summary_month = get_summary_month(user)

        if summary_month <0:
            summary_month = 0;
        today_date = dt.today().strftime('%d/%m/%Y')
        update_past(user)
        current_saving = get_current_saving(user)
        context = {'number':number,'current_saving':current_saving,
                    'today_date': today_date, 'summary_year':summary_year,
                    'summary_month':summary_month }
        return HttpResponse(template.render(context, request))
    else:
        # if user not authenticated send her/him to login page
        return redirect('login/')


def save_concept(request):

    #use case: Save Concept
    number= 3 # variable sent to interface, used to highlight home tab in navbar
    current_user = User.objects.get(id=request.user.id)
    form = Configuration_Form()
    conceptos = get_concepts(current_user)
    template = loader.get_template('config.html')
    message = ""
    if request.method == "POST":
        form = Configuration_Form(request.POST)
        # (save concept) case
        if form.is_valid():
            if(form.cleaned_data['is_new_concept'] == -1):
                message = "NEW CONCEPT CREATED"
                #begin variables:
                name = form.cleaned_data['name']
                value = form.cleaned_data['value']
                period = form.cleaned_data['period']
                type = form.cleaned_data['is_expense']
                #end variables
                newConcept = Concept(name = name, value = value, period = period, type=type, user= current_user)
                newConcept.save()
            else:
                message = "CONCEPT MODIFIED"
                concept = Concept.objects.filter(user=current_user, id=form.cleaned_data['is_new_concept'])[0]
                concept.name = form.cleaned_data['name']
                concept.value = form.cleaned_data['value']
                concept.period = form.cleaned_data['period']
                concept.type= form.cleaned_data['is_expense']
                concept.save()
        else:
            print(form.errors)
    context = {'number':number, 'conceptos': conceptos, 'form': form, 'message':message}
    return HttpResponse(template.render(context, request))


def disable_concept(request):
    #use case: disable concepts
    # function used for ajax

    concept = Concept.objects.get(user__id =request.user.id, id= request.GET['id_concept'])
            # get concept of requsted user with specific id
            # delete first one
    concept.is_disabled = True
    concept.save()
    data = {} #send empty data as json, meaning end of processing
    return HttpResponse(json.dumps(data), content_type="application/json")


def add_daily_input(request):
    # use case: Add daily input
    from .models import Daily_Input
    current_user = User.objects.get(id=request.user.id)


    dailies = Daily_Input.objects.all().filter(user=request.user).order_by('-id').values('value','concept__name', 'concept__type', 'date_from', 'savings_value')
    conceptos = get_concepts(current_user) # variable meant to be sent to interface
    number = 2 # variable sent to interface, used to highlight home tab in navbar
    is_daily_input = False # we dont have any message yet to show to user
    today_date = dt.today().strftime('%d/%m/%Y')
            #default date to be displayed in this interface, is today's date

    message ="" #messages to display to user
    if request.method == 'POST':
        form  = Daily_Input_Form(request.POST)
        is_daily_input = True # we have some message to show to user
        if form.is_valid():
            message = "daily input added"
            # creating new Daily_Input:  (Add daily input)

            #begin variables:
            value=form.cleaned_data['value']
            id_concept = form.cleaned_data['id_concepto']
            concept = Concept.objects.get(id=id_concept)
            from_date = form.cleaned_data['from_date']
            percentage = Savings_Percentage.objects.get(user=current_user).percentage
            is_use_savings = form.cleaned_data['is_use_savings']
            if(is_use_savings == 'False'):
                is_use_savings = False
            else:
                is_use_savings = True
            savings_value = percentage*value
            if(concept.type == True):
                savings_value = 0
            else:
                value-=savings_value
            #end variables
            Daily_Input = Daily_Input(user=current_user, concept=concept, value=value, date_from =from_date , savings_value=savings_value)

            check_if_saving_exist(current_user, Daily_Input.date_from.year,Daily_Input.date_from.month)


            if concept.period == 0 and concept.type == False:
                # if is a concept that has no period and is an income then sum to savings
                # for the refering month and year

                daily_month = Daily_Input.date_from.month
                dailyYear = Daily_Input.date_from.year

                saving = Savings.objects.filter(user= current_user, month=dailyMonth, year=dailyYear)[0]
                saving.value+=savings_value
                saving.save()

                Daily_Input.save()
            elif concept.type == True and concept.period == 0:
                if can_expense(current_user, Daily_Input.value, is_use_savings):
                    if is_use_savings:
                        Daily_Input = Daily_Input(user=current_user, concept=concept, value=value, date_from =from_date , savings_value=savings_value, is_using_savings=True)
                    Daily_Input.save()
                else:
                    message = "don't have enough funds"
            else:
                print(form.errors)
                Daily_Input.save()
        else:
            #form is not valid, dont have all data to create new daily input
            message = "couldn't save this daily input"

    form = Daily_Input_Form()
    template = loader.get_template('Daily_Input.html')
    context = {'number':number, 'conceptos': conceptos, 'today_date':today_date,
                'is_daily_input': is_daily_input, 'form': form, 'message':message,
                'dailies':dailies}
    return HttpResponse(template.render(context, request))

def simulate_balance(request):
    #use case: Simulate Balance
    number = 4 # variable sent to interface, used to highlight home tab in navbar
    user = User.objects.get(id=request.user.id)
    summary_year = 0.00
    summary_month = 0.00

    form = Simulate_Balance_Form()

    is_message = False # tells if there is message to display to the user
    message = ""


    if request.method == 'POST':
        form = Simulate_Balance_Form(request.POST)
        is_message = True
        if form.is_valid():
            value=form.cleaned_data['value']
            from_date = form.cleaned_data['from_date']
            period = form.cleaned_data['period']
            type = form.cleaned_data['is_expense']
            concept = Concept(name = "temporal", value = value, period = period, type=type, user= user)
                #create new concept
            concept.save()
            savings_value = 0.00
            if not type:
                percentage = Savings_Percentage.objects.get(user=user).percentage
                savings_value = value * percentage
            Daily_Input = Daily_Input(user=user, concept=concept, value=value, date_from =from_date , savings_value=savings_value)
                #create daily Input
            Daily_Input.save()
            summary_year = get_summary_year(user) #calculate new summary
            summary_month = get_summary_month(user) #calculate new summary
            Daily_Input.delete() # rollback
            concept.delete() # rollback
            message = "Check your new summary"
        else:
            summary_year = get_summary_year(user)
            summary_month = get_summary_month(user)
            message = "form not valid"
    else:
        summary_year = get_summary_year(user)
        summary_month = get_summary_month(user)

    context ={ 'number':number, 'summary_year':summary_year,
                        'summary_month' : summary_month, 'form':form,
                        'is_message':is_message, 'message':message}

    template = loader.get_template('simulator.html')
    return HttpResponse(template.render(context, request))

def visualize(request):
    #function for use case visualize Expenses && visualize incomes
    type = request.GET['type']
    from_date = dt.strptime(str(request.GET['from']), "%d/%m/%Y")
    to_date = dt.strptime(str(request.GET['to']), "%d/%m/%Y")
    daily_unique = ""
    daily_daily = ""
    daily_biweekly = ""
    daily_monthly = ""
    current_user = User.objects.get(id=request.user.id)


    if type == '1':
        #use case: visualize incomes
        # we should load Incomes
        daily_unique= Daily_Input.objects.filter(user=current_user, concept__period=0, concept__type = False, date_from__gte = from_date, date_from__lte = to_date).order_by('-date_from')

        daily_daily= Daily_Input.objects.all().filter(user=current_user, concept__period=1).filter(concept__type =False,date_from__lte = to_date ).order_by('-date_from')
        if (from_date.day <=14 and to_date.day>=14 and to_date.month == from_date.month )or to_date.month > from_date.month:
            # check if there is some 14th of some month in this range
            daily_biweekly= Daily_Input.objects.filter(user=current_user, concept__period=2, concept__type = False, date_from__lte = to_date).order_by('-date_from')
        if(to_date.month>from_date.month):
            #check if there is some end of month in this range
            daily_monthly= Daily_Input.objects.filter(user=current_user, concept__period=3, concept__type = False, date_from__lte = to_date).order_by('-date_from')
    else:
        #use case: visualize expenses
        # we should load expenses
        daily_unique= Daily_Input.objects.filter(user=current_user, concept__period=0, concept__type =True, date_from__gte = from_date, date_from__lte = to_date).order_by('-date_from')
        daily_daily= Daily_Input.objects.filter(user=current_user, concept__period=1, concept__type =True,  date_from__lte = to_date).order_by('-date_from')
        if (from_date.day <=14 and to_date.day>=14 and to_date.month == from_date.month ) or to_date.month > from_date.month:
            # check if there is some 14th of some month in this range
            daily_biweekly= Daily_Input.objects.filter(user=current_user, concept__period=2, concept__type =True, date_from__lte = to_date).order_by('-date_from')
        if(to_date.month>from_date.month):
            #check if there is some end of month in this range
            daily_monthly= Daily_Input.objects.filter(user=current_user, concept__period=3, concept__type =True, date_from__lte = to_date).order_by('-date_from')

    #begin serialization of each queryset
    json_data_unique= serializers.serialize('json', daily_unique, cls= DjangoJSONEncoder, use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    json_data_daily = serializers.serialize('json', daily_daily, cls= DjangoJSONEncoder,use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    json_data_biweekly = serializers.serialize('json', daily_biweekly, cls= DjangoJSONEncoder,use_natural_foreign_keys=True, fields=('date_from', 'value', 'concept'))
    json_data_monthly = serializers.serialize('json', daily_monthly, cls= DjangoJSONEncoder,use_natural_foreign_keys=True,fields=('date_from', 'value', 'concept'))
    #end serialization of each queryset

    #put all together in a whole json
    json_data = {'unique':json_data_unique,
                'daily': json_data_daily,
                'biweek':json_data_biweekly,
                'monthly':json_data_monthly}
    json_data = {}

    #return json response
    return HttpResponse(json.dumps(json_data), content_type='application/json')


def get_min_date_saving(months):
    # function to calculate since which month should we load savings
    actual_month = dt.now().month
    actual_year = dt.now().year
    if(months < actual_month):
        actual_month-=months
        return actual_month, actual_year
    else:
        while months > actual_month:
            months-=actual_month
            actual_month=12
            actual_year-=1
        return actual_month, actual_year

def get_last_monthly_savings(months, user):
    # get the last savings for the pasten months

    months-=1
    min_month, min_year = get_min_date_saving(months)
    savings = Savings.objects.filter(user=user)
    if min_year == dt.now().year:
        savings = savings.filter(year = dt.now().year, month__gte= dt.now().month - months, month__lte = dt.now().month)
    else:
        savings_part_1 = Savings.objects.filter(year = dt.now().year, month__lte = dt.now().month)
        savings_part_2 = Savings.objects.filter(year = min_year, month__gte = min_month)
        savings_part_3 = Savings.objects.filter(year__gt=min_year, year__lt=dt.now().year)
        savings = savings_part_1 | savings_part_2 |  savings_part_3
        savings = savings.order_by('year').order_by('month')

    return savings

def get_update_user_input_saving(request):
    #use case: visualize savings history
    #function to be called when input in template savings.html changes
    months = int(request.GET['months'])
    savings = get_last_monthly_savings(months, request.user)
    data = serializers.serialize('json', savings)
    return HttpResponse(json.dumps(data), content_type='application/json')


def visualize_savings(request):
    #use case: visualize savings history
    number = 5 # variable sent to interface, used to highlight home tab in navbar5
    savings = get_last_monthly_savings(5, request.user)
    context = {'number':number, 'savings': savings}
    template = loader.get_template('savings.html')
    return HttpResponse(template.render(context, request))
