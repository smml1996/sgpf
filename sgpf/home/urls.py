from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^conf/$', views.save_concept, name='conf'),
	url( r'^change_percentage/$',views.change_savings_percentage,name='change_percentage'),
	url(r'^daily_input/$', views.add_daily_input, name='Daily_Input'),
	url(r'^visualize/$',views.visualize, name="visualize"),
	url(r'^balance_simulator/$',views.simulate_balance, name="simulator"),
	url(r'^savings_history/$',views.visualize_savings, name="savings"),
	url(r'^delete_concept/$', views.disable_concept, name='delete_concept'),
	url(r'^delete_daily/$', views.delete_daily_input, name='delete_daily_input'),
	url(r'^update_saving/$', views.get_update_user_input_saving, name='update_savings'),
	url(r'^$', views.home, name='home'), # default page to be loaded

]
