from datetime import date
from dateutil.relativedelta import relativedelta
from apps.service_requests.models import ServiceRequestActivity


class VisitingChargeCalculatorService:

    '''Class responsible for calculating the visiting charge based on the device's age '''
    VISIT_CHARGE=300.00  
    REPAIR_CHARGE=1000.00
    REPAIR_CHARGE_UNDER_1_YEAR=500.00
    OTHER_CHARGE_UNDER_1_YEAR=300.00
    OTHER_CHAEGE=500.00
    DEFAULT_CHARGE=300.00

    @staticmethod  
    def calculate_visiting_charge(service_type,purchas_date):

        one_year_ago= date.today() - relativedelta(years=1)

        if 'installation' in service_type.lower():
            return 0.00  # No visiting charge for installation services
        
        if 'maintenance' in service_type.lower():
            if purchas_date >= one_year_ago:
                return 0.00  # Zero visiting charge for devices under 1 year old
            return VisitingChargeCalculatorService.VISIT_CHARGE  # Flat visiting charge for devices over 1 year old
            
        if 'repair' in service_type.lower():
              if purchas_date >= one_year_ago:
                 return VisitingChargeCalculatorService.REPAIR_CHARGE_UNDER_1_YEAR  # Flat repair charge for devices under 1 year old
              
              return VisitingChargeCalculatorService.REPAIR_CHARGE  # Flat repair charge for devices over 1 year old
        
        if 'other' in service_type.lower():
            if purchas_date >= one_year_ago:
                return VisitingChargeCalculatorService.OTHER_CHARGE_UNDER_1_YEAR  # Flat charge for other services for devices under 1 year old
            
            return VisitingChargeCalculatorService.OTHER_CHAEGE  # Flat charge for other services for devices over 1 year old
        
        return VisitingChargeCalculatorService.DEFAULT_CHARGE  # Default visiting charge for any other service types
    

class ActivityLogService:
    '''Service class to log activities related to service requests, such as status changes, comments, and user actions, for better transparency and communication between customers and service professionals.'''
    @staticmethod
    def log_activity(service_request,user,comment='',from_status='',to_status=''):
        ServiceRequestActivity.objects.create(
            service_request=service_request,
            user=user,
            comment=comment,
            from_status=from_status,
            to_status=to_status
        )