from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^conf/$', views.SaveConcept, name='conf'),
	url( r'^change_percentage/$',views.changeSavingsPercentage,name='changePercentage'),
	url(r'^daily_input/$', views.AddDailyInput, name='dailyInput'),
	url(r'^visualize/$',views.visualize, name="visualize"),
	url(r'^balance_simulator/$',views.simulateBalance, name="simulator"),
	url(r'^savings_history/$',views.visualizeSavings, name="savings"),
	url(r'^delete_concept/$', views.disableConcept, name='deleteConcept'),
	url(r'^delete_daily/$', views.DeleteDailyInput, name='deleteDailyInput'),
	url(r'^$', views.home, name='home'), # default page to be loaded

]
