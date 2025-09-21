from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_appointment_confirmation_email(appointment):
    """
    Send appointment confirmation email to patient
    
    Args:
        appointment: Appointment instance with patient, doctor, timeslot, and notes
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        patient = appointment.patient
        doctor = appointment.doctor
        timeslot = appointment.timeslot
        
        # Prepare email context
        context = {
            'patient': patient,
            'doctor': doctor,
            'timeslot': timeslot,
            'notes': appointment.notes,
            'appointment_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # Render email templates
        subject = f'Appointment Confirmation - {doctor.user.get_full_name() or doctor.user.username}'
        
        html_message = render_to_string(
            'booking/appointment_confirmation_email.html',
            context
        )
        
        plain_message = render_to_string(
            'booking/appointment_confirmation_email.txt',
            context
        )
        
        # Send email
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [patient.email]
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        
        if result:
            logger.info(f"Appointment confirmation email sent successfully to {patient.email} for appointment {appointment.id}")
            return True
        else:
            logger.error(f"Failed to send appointment confirmation email to {patient.email} for appointment {appointment.id}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending appointment confirmation email for appointment {appointment.id}: {str(e)}")
        return False


def send_appointment_confirmation_email_safe(appointment):
    """
    Safe version of send_appointment_confirmation_email that doesn't raise exceptions
    and logs errors appropriately
    
    Args:
        appointment: Appointment instance
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        return send_appointment_confirmation_email(appointment)
    except Exception as e:
        logger.error(f"Safe email sending failed for appointment {appointment.id}: {str(e)}")
        return False
