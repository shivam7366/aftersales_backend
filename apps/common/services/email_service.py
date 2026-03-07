from django.core.mail import send_mail
from django.conf import settings

class EmailService:

    '''Service class to handle email sending operations using Django's built-in email functionality.'''
    
    @staticmethod
    def send_email(subject, message, recipient_list, from_email=settings.DEFAULT_FROM_EMAIL):
        try:

            send_mail(subject, message, from_email, recipient_list)
            return True
        except Exception as e:
            # Log the error or handle it as needed
            print(f"Error sending email: {str(e)}")
            return False
        

    @staticmethod
    def send_password_reset_email(email, reset_url):
        subject = 'Password Reset Request'
        message = (
            'You requested a password reset.\n\n'
            'Click the link below to reset your password:\n\n'
            f'{reset_url}\n\n'
            'This link is valid for 30 minutes.\n\n'
            'If you did not request this, please ignore this email.'
        )
        return EmailService.send_email(subject, message, [email])
    
    @staticmethod
    def send_otp_email(email, otp):
        subject = 'Email Verification'
        message = f'Your OTP for email verification is: {otp}\n\nThis OTP is valid for 5 minutes.'        
        return EmailService.send_email(subject, message, [email])
