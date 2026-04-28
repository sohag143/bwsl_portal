from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # কোন কোন কলামগুলো সরাসরি দেখবেন
    list_display = ('date', 'purpose', 'transaction_type', 'amount', 'user') 
    
    # ডানপাশে ফিল্টার অপশন যোগ করা
    list_filter = ('user', 'transaction_type', 'date') 
    
    # সার্চ বার যোগ করা
    search_fields = ('purpose', 'user__username')

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)