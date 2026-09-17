from django.urls import path
from accounts.views import (
    patient_activate, patient_register, patient_login, patient_me,
    doctor_login, doctor_me, doctor_register, register_fcm_token,
    change_password
)

urlpatterns = [
    path('activate/', patient_activate, name='patient_activate'),
    path('register/', patient_register, name='patient_register'),
    path('login/', patient_login, name='patient_login'),
    path('me/', patient_me, name='patient_me'),
    path('doctor/login/', doctor_login, name='doctor_login'),
    path('doctor/me/', doctor_me, name='doctor_me'),
    path('doctor/register/', doctor_register, name='doctor_register'),
    path('register-fcm-token/', register_fcm_token, name='register_fcm_token'),
    path('change-password/', change_password, name='change_password'),
]


