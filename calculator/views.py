from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Transaction, Purpose
from django.db.models import Sum, Q

@login_required
def index(request):
    # ড্যাশবোর্ডের ব্যালেন্স ক্যালকুলেশন
    total_in = Transaction.objects.filter(transaction_type='IN').aggregate(Sum('amount'))['amount__sum'] or 0
    total_out = Transaction.objects.filter(transaction_type='OUT').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_in - total_out
    
    # ড্যাশবোর্ডে রিসেন্ট ৫টি হিস্টোরি
    history = Transaction.objects.all().order_by('-date', '-id')[:5]

    return render(request, 'calculator/index.html', {
        'total_in': total_in,
        'total_out': total_out,
        'balance': balance,
        'history': history,
    })

# নতুন Purpose এন্ট্রি করার ফাংশন
@login_required
def purpose_entry(request):
    if request.method == "POST":
        p_name = request.POST.get('purpose_name')
        if p_name:
            Purpose.objects.get_or_create(name=p_name) # একই নাম বারবার সেভ হবে না
            messages.success(request, f"'{p_name}' পারপাস হিসেবে যোগ করা হয়েছে!")
            return redirect('purpose_entry')
    return render(request, 'calculator/purpose_entry.html')

@login_required
def deposit_entry(request):
    purposes = Purpose.objects.all() # ড্রপডাউনের জন্য সব পারপাস নিয়ে আসা
    if request.method == 'POST':
        date = request.POST.get('date')
        purpose = request.POST.get('purpose')
        amount = request.POST.get('amount')
        remarks = request.POST.get('remarks')

        if date and purpose and amount:
            Transaction.objects.create(
                user=request.user,
                date=date,
                purpose=purpose,
                amount=amount,
                transaction_type='IN',
                remarks=remarks
            )
            messages.success(request, "সফলভাবে জমা (Deposit) করা হয়েছে!")
            return redirect('deposit_entry')
        else:
            messages.error(request, "সবগুলো ঘর পূরণ করুন!")
            
    return render(request, 'calculator/deposit.html', {'purposes': purposes})

@login_required
def payment_entry(request):
    purposes = Purpose.objects.all() # ড্রপডাউনের জন্য সব পারপাস নিয়ে আসা
    if request.method == 'POST':
        date = request.POST.get('date')
        purpose = request.POST.get('purpose')
        amount = request.POST.get('amount')
        remarks = request.POST.get('remarks')

        if date and purpose and amount:
            Transaction.objects.create(
                user=request.user,
                date=date,
                purpose=purpose,
                amount=amount,
                transaction_type='OUT',
                remarks=remarks
            )
            messages.success(request, "পেমেন্ট (Payment) সফলভাবে সেভ হয়েছে!")
            return redirect('payment_entry')
        else:
            messages.error(request, "সবগুলো তথ্য দিন!")

    return render(request, 'calculator/payment.html', {'purposes': purposes})

@login_required
def transaction_history(request):
    all_transactions = Transaction.objects.all().order_by('-date', 'id')
    return render(request, 'calculator/transaction_history.html', {'transactions': all_transactions})

@login_required
def delete_transaction(request, pk):
    try:
        transaction = Transaction.objects.get(id=pk)
        transaction.delete()
        messages.warning(request, "হিসাবটি সফলভাবে ডিলিট করা হয়েছে।")
    except Transaction.DoesNotExist:
        messages.error(request, "লেনদেনটি খুঁজে পাওয়া যায়নি।")
    
    return redirect(request.META.get('HTTP_REFERER', 'transaction_history'))

def purpose_entry(request):
    if request.method == "POST":
        purpose_name = request.POST.get('purpose_name')
        if purpose_name:
            Purpose.objects.create(name=purpose_name)
            messages.success(request, "New Purpose added successfully!")
            return redirect('purpose_entry')
    
    purposes = Purpose.objects.all()
    return render(request, 'calculator/purpose_entry.html', {'purposes': purposes})


def purpose_summary(request, purpose_name):

    total_credit = Transaction.objects.filter(
        Q(purpose__iexact=purpose_name), 
        Q(transaction_type__iexact='credit') | Q(transaction_type__iexact='IN')
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_debit = Transaction.objects.filter(
        Q(purpose__iexact=purpose_name), 
        Q(transaction_type__iexact='debit') | Q(transaction_type__iexact='OUT')
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    balance = float(total_credit) - float(total_debit)
    
    context = {
        'purpose_title': purpose_name,
        'total_credit': total_credit,
        'total_debit': total_debit,
        'balance': balance,
    }
    return render(request, 'calculator/purpose_summary.html', context)

import csv
from django.http import HttpResponse
from .models import Transaction

def export_transactions_excel(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    transactions = Transaction.objects.all()
    if from_date and to_date:
        transactions = transactions.filter(date__range=[from_date, to_date])

    response = HttpResponse(content_type='text/csv')
    response ['Content-Disposition'] = 'attachment; filename = "Transactions_csv"'
    
    writer = csv.writer(response)
    writer.writerow (['Date', 'Type', 'Amount', 'Remarks'])

    for obj in transactions:
        writer.writerow([obj.date, obj.transaction_type, obj.amount, obj.remarks])
    return response