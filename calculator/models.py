from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError 
import datetime

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    TRANSACTION_TYPES = (('IN', 'Cash In'), ('OUT', 'Payment/Expense'))
    def validate_year(value):
        if value.year > 9999:
            raise ValidationError('Year not more than 4 digit')
    date = models.DateField(models.DateField(validators=[validate_year]))
    purpose = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.purpose} - {self.amount}"
    

class Purpose(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    

    

