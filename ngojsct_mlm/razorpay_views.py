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
import datetime
from .models import PaymentRequestDetailsModel,MemberModel , PaymentResponseDetailsModel #, CustomUser  # Ensure Order and Product models are defined

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
# FRONTEND_HOST = "http://127.0.0.1:3000"


class CheckoutView(View):
    permission_classes = [AllowAny]

    def get(self, request,id):
        member_details=MemberModel.objects.filter(id=id).first()
        # return Response({"message": "Checkout page loaded"}, status=200)
        return render(request, "checkoutview.html",{'member_details':member_details})

@method_decorator(csrf_exempt,name='dispatch')
class InitiatePaymentView(View):
    def post(self, request,id):
        print('ididii',id)

        order_data = {
            "amount": 155100, #In paisa
            "currency": "INR",
            "payment_capture": 1,
        }
        
        razorpay_order = client.order.create(order_data)
        print(razorpay_order)
        # Save order in your DB
        PaymentRequestDetailsModel.objects.create(
            request_text   =     razorpay_order   ,       
            success_status =     True     ,
            # payemnt_code   =  
            payment_gatway_name= 'Razorpay'  ,             
            # message                       
            # merchantId                    
            # merchantTransactionId         
            # instrumentResponse_type       
            # instrumentResponse_redirect   
            # method_type                   
            # checksum                      
            amount         =       razorpay_order["amount"] / 100,  # Convert to rupees   
            attempts        =       razorpay_order["attempts"],
            member_id         =           id  ,
            # ngo                         
            # campaign                    
            pay_for       =         'Registration'   ,      
            currency        =       'INR',
            # name                          
            # email                         
            # mobile                        
            is_indian        = True   ,
            order_id        =          razorpay_order["id"],
            # make_donation_anonymous     
            # receive_whatsapp_updates    
            # tip_amount          
            status                  =      razorpay_order["status"],  
        )

        # update_status=MemberModel.objects.filter()

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
                check_req=PaymentRequestDetailsModel.objects.filter(order_id=order_id).first()
                if check_req:
                    payment_response_create_db=PaymentResponseDetailsModel.objects.create(
                        member_id=check_req.member_id,
                        request_text  =   data    ,
                        razorpay_payment_id  = payment_id,
                        razorpay_order_id    = order_id,
                        razorpay_signature   = signature,
                        created_at          = datetime.datetime.now(),
                    )
                    update_status=MemberModel.objects.filter(id=check_req.member_id).update(status=2,is_active=True)
                    if update_status:
                        return redirect(f'/payment-receipt/{payment_response_create_db.razorpay_order_id}')
                # return JsonResponse({"status": "success"})
            except razorpay.errors.SignatureVerificationError:
                # order.is_paid = False
                # order.save()
                return JsonResponse({"status": "failed", "reason": "Signature verification failed"}, status=400)

        except Exception as e:
            logging.error(f"Payment callback error: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseServerError
from django.views import View

from .models import PaymentResponseDetailsModel

logger = logging.getLogger(__name__)

class PaymentReceiptView(View):
    def get(self, request, id):
        if True:
        # try:
            response = get_object_or_404(PaymentResponseDetailsModel, razorpay_order_id=id)
            # user = response.user
            request_pymt=get_object_or_404(PaymentRequestDetailsModel, order_id=id)
            payment_status = "PAID" #if response.is_paid else "UNPAID"
            data = {
                "receipt": {
                    "order_id": response.razorpay_order_id,
                    "payment_id": response.razorpay_payment_id,
                    "status": payment_status,
                    # "amount": int(response.amount * 100),
                    # "product": response.product.name,
                },
                "request_pymt":request_pymt
                # "user": {
                #     "name": getattr(user, "name", getattr(user, "username", "")),
                #     "email": user.email,
                # }
            }
            return render(request, 'payment_receipt_view.html', data)

        # except Exception as e:
        #     logger.error(f"Error in fetching receipt: {e}")
        #     return HttpResponseServerError("Unable to fetch receipt")




"""
#Razorpay Request Order Example Response
{'amount': 1000, 'amount_due': 1000, 'amount_paid': 0, 'attempts': 0, 'created_at': 1752028219, 'currency': 'INR', 'entity': 'order', 'id': 'order_QqnwWvLd9ImHRP', 'notes': [], 'offer_id': None, 'receipt': None, 'status': 'created'}
"""


"""#Razorpay Response Order Example Response
<QueryDict: {'razorpay_payment_id': ['pay_QqoRQ1ofD0wlhr'], 'razorpay_order_id': ['order_QqoRFFi8OXzQ01'], 'razorpay_signature': ['34c9199d2052a83c58c843814c565615e7a072122797322daafc2e26917569c2']}>

"""