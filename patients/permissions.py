from rest_framework import permissions

class IsClinicalStaffOrOwner(permissions.BasePermission):
    """
    Custom Permission for TSPI EMR:
    - Admin/Doctor/Nurse: Can read and write all patient records.
    - Patient: Can only access their own profile and biological records.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # 1. Staff (Doctors, Nurses, Admins) have full access
        if user.is_staff or user.groups.filter(name__in=['admin', 'doctor', 'nurse']).exists():
            return True
            
        # 2. Check if the object belongs to the logged-in patient
        from patients.models import Patient, PatientBiologicalRecord, PatientHistory, Appointment
        
        if isinstance(obj, Patient):
            return obj.id_card == user.username
            
        if isinstance(obj, PatientBiologicalRecord):
            return obj.patient.id_card == user.username
            
        if isinstance(obj, PatientHistory):
            return obj.patient.id_card == user.username
            
        if isinstance(obj, Appointment):
            # Check matching appointment fields against patient legacy profiles
            patient = Patient.objects.filter(id_card=user.username).first()
            if patient:
                return obj.userid in [patient.legacy_id, patient.hn, patient.id_card, patient.phone]
            return obj.userid == user.username
            
        # Default fallback
        if hasattr(obj, 'patient'):
            return obj.patient.id_card == user.username
            
        return False
