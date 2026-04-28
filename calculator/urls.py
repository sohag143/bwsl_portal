from django.urls import path
from . import views

urlpatterns = [
    # views.dashboard এর বদলে views.index ব্যবহার করা হয়েছে
    path('', views.index, name='index'), 
    path('deposit/', views.deposit_entry, name='deposit_entry'),
    path('payment/', views.payment_entry, name='payment_entry'),
    path('purpose-entry/', views.purpose_entry, name='purpose_entry'),
    path('history/', views.transaction_history, name='transaction_history'),
    path('delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('summary/<str:purpose_name>/', views.purpose_summary, name='purpose_summary'),
    path('export/exce;/', views.export_transactions_excel, name='export_excel'),
]