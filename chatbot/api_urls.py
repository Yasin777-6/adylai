from django.urls import path
from . import api_views

app_name = 'chatbot_api'

urlpatterns = [
    path('start/', api_views.StartChatAPIView.as_view(), name='start_chat'),
    path('send/', api_views.SendMessageAPIView.as_view(), name='send_message'),
    path('contact/', api_views.SubmitContactAPIView.as_view(), name='submit_contact'),
    path('schedule/', api_views.ScheduleAppointmentAPIView.as_view(), name='schedule_appointment'),
    path('history/', api_views.GetChatHistoryAPIView.as_view(), name='chat_history'),
] 