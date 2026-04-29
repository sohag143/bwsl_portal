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

import csv
import io
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Transaction, Purpose

def payment_entry(request):
    if request.method == "POST":
        entry_type = request.POST.get('entry_type')
        action = request.POST.get('action') # বাটন চেক করার জন্য: upload অথবা process
        
        # ১. ম্যানুয়াল এন্ট্রি
        if entry_type == 'manual':
            date = request.POST.get('date')
            purpose = request.POST.get('purpose')
            amount = request.POST.get('amount')
            remarks = request.POST.get('remarks')
            
            Transaction.objects.create(
                date=date,
                purpose=purpose,
                amount=amount,
                transaction_type='OUT',
                remarks=remarks
            )
            messages.success(request, "Manual entry saved!")

        # ২. CSV ফাইল এন্ট্রি (আপডেট করা লজিক)
        elif entry_type == 'bulk':
            # ইউজার যখন 'Upload' বাটনে ক্লিক করবে
            if action == 'upload':
                csv_file = request.FILES.get('excel_file')
                if not csv_file or not csv_file.name.endswith('.csv'):
                    messages.error(request, 'দয়া করে একটি সঠিক .csv ফাইল সিলেক্ট করে Upload এ ক্লিক করুন।')
                else:
                    messages.info(request, f"ফাইল '{csv_file.name}' আপলোড হয়েছে। এখন নিচের বাটনে ক্লিক করে প্রসেস করুন।")

            # ইউজার যখন 'Process' বাটনে ক্লিক করবে
            elif action == 'process':
                date = request.POST.get('date')
                purpose = request.POST.get('purpose')
                bulk_remarks = request.POST.get('bulk_remarks', '') # টেমপ্লেটের নতুন রিমার্কস বক্স
                csv_file = request.FILES.get('excel_file')

                if not csv_file:
                    messages.error(request, "প্রসেস করার আগে ফাইল আপলোড করা প্রয়োজন।")
                    return redirect('payment_entry')

                try:
                    data_set = csv_file.read().decode('UTF-8')
                    io_string = io.StringIO(data_set)
                    next(io_string) # হেডার রো বাদ দেওয়ার জন্য

                    for row in csv.reader(io_string, delimiter=',', quotechar="|"):
                        bkash_no = row[0].strip()
                        amount = row[1].strip()
                        
                        # বিকাশ নম্বর চেক করে স্ট্যাটাস নির্ধারণ
                        if bkash_no and bkash_no.lower() != 'nan' and bkash_no != '':
                            status_remarks = f"Bkash: {bkash_no} | Status: PAID | {bulk_remarks}"
                        else:
                            status_remarks = f"No Bkash Number | Status: UNPAID | {bulk_remarks}"

                        Transaction.objects.create(
                            date=date,
                            purpose=purpose,
                            amount=amount,
                            transaction_type='OUT',
                            remarks=status_remarks
                        )
                    messages.success(request, f"CSV ফাইল থেকে সফলভাবে {purpose} এন্ট্রি প্রসেস করা হয়েছে।")
                except Exception as e:
                    messages.error(request, f"ফাইল প্রসেস করতে সমস্যা হয়েছে: {e}")

        return redirect('payment_entry')

    purposes = Purpose.objects.all()
    return render(request, 'calculator/payment.html', {'purposes': purposes})


@login_required
def transaction_history(request):
    all_transactions = Transaction.objects.all().order_by('-date', '-created_at')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    search_query = request.GET.get('search')
    if from_date and to_date:
        all_transactions = all_transactions.filter(date__range=[from_date, to_date])
    if search_query:
        all_transactions = all_transactions.filter(Q(purpose__icontains=search_query) | Q(remarks__icontains=search_query))
        
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

    transactions = Transaction.objects.all().order_by('-date')
    if from_date and to_date:
        transactions = transactions.filter(date__range=[from_date, to_date])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="BWSL_Transactions.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['Date', 'Purpose', 'Type', 'Amount', 'Remarks'])

    for obj in transactions:
        writer.writerow([
            obj.date.strftime('%d-%m-%Y') if obj.date else '', 
            obj.purpose, 
            obj.transaction_type, 
            obj.amount, 
            obj.remarks if obj.remarks else '---'
        ])
    return response


# স্যালারি পেইড লিস্ট
@login_required
def salary_paid_list(request):
    # যে সকল Salary এন্ট্রিতে রিমার্কস বা বিকাশ নাম্বার আছে
    paid_salary = Transaction.objects.filter(
        Q(purpose__iexact='Salary'),
        ~Q(remarks__isnull=True), ~Q(remarks='')
    ).order_by('-date', '-created_at')
    
    return render(request, 'calculator/unpaid_list.html', {
        'title': 'Salary Paid List',
        'transactions': paid_salary
    })

# টিফিন বিল পেইড লিস্ট
@login_required
def tiffin_paid_list(request):
    paid_tiffin = Transaction.objects.filter(
        Q(purpose__iexact='Tiffin & Holiday Bill'),
        ~Q(remarks__isnull=True), ~Q(remarks='')
    ).order_by('-date', '-created_at')
    
    return render(request, 'calculator/unpaid_list.html', {
        'title': 'Tiffin & Holiday Bill Paid List',
        'transactions': paid_tiffin
    })


# স্যালারি আনপেইড লিস্ট
@login_required
def salary_unpaid_list(request):
    # যে সকল Salary এন্ট্রিতে বিকাশ নাম্বার বা রিমার্কস নেই (ফাঁকা)
    unpaid_salary = Transaction.objects.filter(
        Q(purpose__iexact='Salary'),
        Q(remarks__isnull=True) | Q(remarks='')
    ).order_by('-date')
    
    return render(request, 'calculator/unpaid_list.html', {
        'title': 'Salary Unpaid List',
        'transactions': unpaid_salary
    })

# টিফিন বিল আনপেইড লিস্ট
@login_required
def tiffin_unpaid_list(request):
    unpaid_tiffin = Transaction.objects.filter(
        Q(purpose__iexact='Tiffin & Holiday Bill'),
        Q(remarks__isnull=True) | Q(remarks='')
    ).order_by('-date')
    
    return render(request, 'calculator/unpaid_list.html', {
        'title': 'Tiffin & Holiday Bill Unpaid List',
        'transactions': unpaid_tiffin
    })

from collections import defaultdict
from django.shortcuts import render
from .models import Transaction

def history_summary(request):
    # সকল ট্রানজ্যাকশন তারিখ অনুযায়ী পুরনো থেকে নতুন হিসেবে নিন (যাতে ব্যালেন্স শুরু থেকে যোগ হয়)
    transactions = Transaction.objects.all().order_by('date')
    
    summary_dict = defaultdict(lambda: {'deposit': 0.0, 'payment': 0.0})

    # প্রথমে প্রতিটি তারিখ ও পারপাস অনুযায়ী জমা ও খরচ আলাদা করুন
    for tx in transactions:
        key = (tx.date, tx.purpose)
        amount = float(tx.amount) if tx.amount else 0.0
        
        if tx.transaction_type == 'IN':
            summary_dict[key]['deposit'] += amount
        else:
            summary_dict[key]['payment'] += amount

    # এবার তারিখ অনুযায়ী রানিং ব্যালেন্স ক্যালকুলেট করুন
    sorted_keys = sorted(summary_dict.keys())
    final_summary = []
    running_balance = 0.0

    for key in sorted_keys:
        date, purpose = key
        deposit = summary_dict[key]['deposit']
        payment = summary_dict[key]['payment']
        
        # রানিং ব্যালেন্সের সাথে আজকের জমা যোগ এবং খরচ বিয়োগ
        running_balance += (deposit - payment)
        
        final_summary.append({
            'date': date,
            'purpose': purpose,
            'deposit': deposit,
            'payment': payment,
            'balance': running_balance  # এখন এটি আগের ডিপোজিট হিসেব করেই আসবে
        })

    # ডিসপ্লে করার জন্য নতুন ডাটা উপরে রাখুন (Reverse list)
    final_summary.reverse()

    return render(request, 'calculator/history_summary.html', {'summary_list': final_summary})