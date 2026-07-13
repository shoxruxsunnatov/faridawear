from datetime import timedelta

from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from account.models import User
from payment.models import Transaction

from account.security import (
    AdminRoleRequired,
    CSRFExempt
)


class TeacherStudentPaymentViewAPI(CSRFExempt, AdminRoleRequired, View):

    def post(self, req, pk, *args, **kwargs):
        
        student = get_object_or_404(User, id=pk)

        amount = req.POST.get('amount', '')
        data = {
            "message": "failed",
            "error": None
        }

        try:
            amount = int(amount)
            if not 0 < amount < 1000000:
                raise ValueError
        except:
            data["error"] = 'amount'
        
        if not data["error"]:
            student.balance += amount
            student.save()

            transaction = Transaction(
                user=student,
                amount=amount,
                category="deposit",
                group=student.group,
                organization=student.organization,
                created_by=req.user
            )
            transaction.save()

            data["message"] = "success"

        return JsonResponse(data, safe=False)
    

    def get(self, req, pk, *args, **kwargs):

        student = get_object_or_404(User, id=pk)
        
            
        data = {
            "id": student.id,
            "full_name": student.get_full_name(),
            "balance": student.balance,
            "is_paid": student.is_paid,
            "payment_due": student.payment_due,
            "tuition_cost": student.tuition_cost
        }

        data["transactions"] = [
            {
                "amount": transaction.amount,
                "category": transaction.category,
                "created_by": transaction.created_by.get_full_name()
                if transaction.created_by else "platform",
                "date_created": transaction.date_created,
            }
            for transaction in student.transactions.all()
        ]
            
        return JsonResponse(data, safe=False)


class StudentPaymentSettingsAPI(CSRFExempt, AdminRoleRequired, View):

    def post(self, req, pk, *args, **kwargs):
        
        student = get_object_or_404(User, id=pk)

        setting = req.POST.get('setting')

        data = {
            "message": "failed",
            "errors": []
        }

        if setting == 'free-access':
            try:
                hours = int(req.POST.get('hours'))
                if not 0 <= hours < 169:
                    raise ValueError
            except:
                data["errors"].append('hours')
            
            if student.payment_due:
                data["errors"].append('payment-due')
            
            if not data["errors"]:
                student.payment_due = timezone.now() + timedelta(hours=hours)
                student.is_paid = True
                student.save()
            
                data["message"] = "success"

        elif setting == 'manual-charge':
            if student.tuition_cost and student.tuition_cost > 0:
                if student.tuition_cost > student.balance:
                    data["errors"].append("funds")
            else:
                data["errors"].append("tuition-cost")

            if student.is_paid:
                data["errors"].append("already-active")
            
            if not data["errors"]:
                student.balance -= student.tuition_cost
                student.is_paid = True
                student.payment_due += timedelta(days=30)
                student.save()

                transaction = Transaction(
                    user=student,
                    amount=-student.tuition_cost,
                    category="charge-tuition",
                    group=student.group,
                    organization=student.organization,
                    created_by=req.user
                )
                transaction.save()

                data["message"] = "success"
            
        elif setting == 'tuition-cost-set':
            try:
                tuition_cost = int(req.POST.get('tuition-cost'))
                if not 100 <= tuition_cost:
                    raise ValueError
            except:
                data["errors"].append('tuition-cost')
            
            if not data["errors"]:
                student.tuition_cost = tuition_cost
                student.save()
            
                data["message"] = "success"
            
        return JsonResponse(data, safe=False)
    
