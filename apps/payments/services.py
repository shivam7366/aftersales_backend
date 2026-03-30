import hmac
import hashlib
import razorpay
from django.conf import settings

class RazorpayService:
    def __init__(self):
        self.client=razorpay.client(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET)
    
    def create_order(self,amount:float)->dict:
        data={
            'amount':int(amount*100),
            'currency':'INR',
            'payment_capture':1
        }
        
        return self.client.order.create(data=data)

    def verfiy_signature(self,razorpay_order_id:str,razorpay_payment_id:str,razorpay_signature:str)->bool:
        message=f"{razorpay_order_id}|{razorpay_payment_id}"
        generated_signature=hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(generated_signature, razorpay_signature)
    