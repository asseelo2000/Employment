from django.urls import include, path
from . import views
from helpdesk.views.public import create_ticket
from .views import CustomPublicTicketView

app_name = 'employment'

urlpatterns = [
    path("", views.signup, name="signup"),
    path('index/', views.index, name='index'), 
    path("sign_in/", views.sign_in, name="sign_in"),
    path("all_jobs/", views.all_jobs, name="all_jobs"),
    path("job_detail/<int:myid>/", views.job_detail, name="job_detail"),
    path("job_apply/<int:myid>/", views.job_apply, name="job_apply"),
    # path('helpdesk/tickets/submit/', CustomPublicTicketView.as_view(), name='helpdesk_submit'),
    # path('submit-issue/', views.submit_issue, name='submit_issue'),
    
    path('helpdesk/tickets/submit/', create_ticket, name='helpdesk_submit'),
    path('feedback/', views.receive_feedback, name='receive_feedback'),
    
    path('helpdesk/', include('helpdesk.urls')),
    path('helpdesk/tickets/', views.ticket_list, name='helpdesk_ticket_list'),
    path('helpdesk/tickets/<int:ticket_id>/', views.view_ticket, name='helpdesk_view_ticket'),
    path('send-feedback/<int:ticket_id>/', views.send_internal_feedback, name='send_internal_feedback'),
    path('send-external-ticket/<int:ticket_id>/', views.send_external_ticket, name='send_external_ticket'),

    ]
