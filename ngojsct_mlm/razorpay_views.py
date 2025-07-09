# from rest_framework.views import APIView
from django.views import View
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
import logging
import razorpay
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import PaymentRequestDetailsModel #, PaymentResponseDetailsModel, CustomUser  # Ensure Order and Product models are defined

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
# FRONTEND_HOST = "http://127.0.0.1:3000"


class CheckoutView(View):
    permission_classes = [AllowAny]

    def get(self, request):
        # return Response({"message": "Checkout page loaded"}, status=200)
        return render(request, "checkoutview.html",)

@method_decorator(csrf_exempt,name='dispatch')
class InitiatePaymentView(View):
    def post(self, request,):
        

        order_data = {
            "amount": 1000,
            "currency": "INR",
            "payment_capture": 1,
        }

        razorpay_order = client.order.create(order_data)
        # print(razorpay_order)
        # Save order in your DB
        # PaymentRequestDetailsModel.objects.create(
        #     request_text   =     razorpay_order          
        #     success_status =     True     
        #     payemnt_code   =                 
        #     message                       
        #     merchantId                    
        #     merchantTransactionId         
        #     instrumentResponse_type       
        #     instrumentResponse_redirect   
        #     method_type                   
        #     checksum                      
        #     amount         =       razorpay_order["amount"] / 100,  # Convert to rupees       
        #     member         =             
        #     # ngo                         
        #     # campaign                    
        #     pay_for                       
        #     name                          
        #     email                         
        #     mobile                        
        #     is_indian                     
        #     # make_donation_anonymous     
        #     # receive_whatsapp_updates    
        #     # tip_amount                  
        # )

        return JsonResponse({
            "order_id": razorpay_order["id"],
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
           
            "amount": order_data["amount"],
            "razorpay_callback_url": settings.RAZORPAY_CALLBACK_URL,
        })

@method_decorator(csrf_exempt,name='dispatch')
class PaymentCallbackView(View):
    # permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.POST or request.data
            print(data)
            order_id = data.get("razorpay_order_id")
            payment_id = data.get("razorpay_payment_id")
            signature = data.get("razorpay_signature")

            if not (order_id and payment_id and signature):
                return JsonResponse({"status": "failed", "reason": "Missing parameters"}, status=400)

            # order = get_object_or_404(Order, razorpay_order_id=order_id)

            # Verify the signature
            # PaymentResponseDetailsModel
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }

            try:
                client.utility.verify_payment_signature(params_dict)
                # order.razorpay_payment_id = payment_id
                # order.razorpay_signature = signature
                # order.is_paid = True
                # order.save()
                return JsonResponse({"status": "success"})
            except razorpay.errors.SignatureVerificationError:
                # order.is_paid = False
                # order.save()
                return JsonResponse({"status": "failed", "reason": "Signature verification failed"}, status=400)

        except Exception as e:
            logging.error(f"Payment callback error: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class PaymentReceiptView(View):
    permission_classes = [AllowAny]

    def get(self, request, order_id):
        try:
            reponse = get_object_or_404(PaymentResponseDetailsModel, razorpay_order_id=order_id)
            user = reponse.user

            payment_status = "PAID" if reponse.is_paid else "UNPAID"

            return Response({
                "receipt": {
                    "order_id": reponse.razorpay_order_id,
                    "payment_id": reponse.razorpay_payment_id,
                    "status": payment_status,
                    "amount": int(reponse.amount * 100),
                    "product": reponse.product.name,
                },
                "user": {
                    "name": getattr(user, "name", user.username),
                    "email": user.email,
                }
            }, status=200)

        except Exception as e:
            logging.error(f"Error in fetching receipt: {e}")
            return Response({"error": "Unable to fetch receipt"}, status=500)



"""
#Razorpay Request Order Example Response
{'amount': 1000, 'amount_due': 1000, 'amount_paid': 0, 'attempts': 0, 'created_at': 1752028219, 'currency': 'INR', 'entity': 'order', 'id': 'order_QqnwWvLd9ImHRP', 'notes': [], 'offer_id': None, 'receipt': None, 'status': 'created'}
"""


"""#Razorpay Response Order Example Response
<QueryDict: {'razorpay_payment_id': ['pay_QqoRQ1ofD0wlhr'], 'razorpay_order_id': ['order_QqoRFFi8OXzQ01'], 'razorpay_signature': ['34c9199d2052a83c58c843814c565615e7a072122797322daafc2e26917569c2']}>

"""