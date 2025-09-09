# Django core imports
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# Authentication and permissions
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Class-based views
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView
)

# Third-party packages
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

# Local app imports
from .models import Profile, Customer, Vendor,STATUS_CHOICES, ROLE_CHOICES
from .forms import (
    CreateUserForm, UserUpdateForm,
    ProfileUpdateForm, CustomerForm,
    VendorForm
)
from .tables import ProfileTable


def register(request):
    """
    Handle user registration.
    If the request is POST, process the form data to create a new user.
    Redirect to the login page on successful registration.
    For GET requests, render the registration form.
    """
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user-login')
    else:
        form = CreateUserForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    """
    Render the user profile page.
    Requires user to be logged in.
    """
    return render(request, 'accounts/profile.html')


@login_required
def profile_update(request):
    """
    Handle profile update.
    If the request is POST, process the form data
    to update user information and profile.
    Redirect to the profile page on success.
    For GET requests, render the update forms.
    """
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('user-profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(
        request,
        'accounts/profile_update.html',
        {'u_form': u_form, 'p_form': p_form}
    )


class ProfileListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    """
    Display a list of profiles in a table format.
    Requires user to be logged in
    and supports exporting the table data.
    Pagination is applied with 10 profiles per page.
    """
    model = Profile
    template_name = 'accounts/stafflist.html'
    context_object_name = 'profiles'
    table_class = ProfileTable
    paginate_by = 10
    table_pagination = False


class ProfileCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new profile.
    Requires user to be logged in and have superuser status.
    Redirects to the profile list upon successful creation.
    """
    model = Profile
    template_name = 'accounts/staffcreate.html'
    fields = ['user', 'role', 'status']

    def get_success_url(self):
        """
        Return the URL to redirect to after successfully creating a profile.
        """
        return reverse('profile_list')

    def test_func(self):
        """
        Check if the user is a superuser.
        """
        return self.request.user.is_superuser


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing profile.
    Requires user to be logged in and have superuser status.
    Redirects to the profile list upon successful update.
    """
    model = Profile
    template_name = 'accounts/staffupdate.html'
    fields = ['user', 'role', 'status']

    def get_success_url(self):
        """
        Return the URL to redirect to after successfully updating a profile.
        """
        return reverse('profile_list')

    def test_func(self):
        """
        Check if the user is a superuser.
        """
        return self.request.user.is_superuser


class ProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete an existing profile.
    Requires user to be logged in and have superuser status.
    Redirects to the profile list upon successful deletion.
    """
    model = Profile
    template_name = 'accounts/staffdelete.html'

    def get_success_url(self):
        """
        Return the URL to redirect to after successfully deleting a profile.
        """
        return reverse('profile_list')

    def test_func(self):
        """
        Check if the user is a superuser.
        """
        return self.request.user.is_superuser


class CustomerListView(LoginRequiredMixin, ListView):
    """
    View for listing all customers.

    Requires the user to be logged in. Displays a list of all Customer objects.
    """
    model = Customer
    template_name = 'accounts/customer_list.html'
    context_object_name = 'customers'


class CustomerCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new customer.

    Requires the user to be logged in.
    Provides a form for creating a new Customer object.
    On successful form submission, redirects to the customer list.
    """
    model = Customer
    template_name = 'accounts/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating an existing customer.

    Requires the user to be logged in.
    Provides a form for editing an existing Customer object.
    On successful form submission, redirects to the customer list.
    """
    model = Customer
    template_name = 'accounts/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting a customer.

    Requires the user to be logged in.
    Displays a confirmation page for deleting an existing Customer object.
    On confirmation, deletes the object and redirects to the customer list.
    """
    model = Customer
    template_name = 'accounts/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@csrf_exempt
@require_POST
@login_required
def get_customers(request):
    if is_ajax(request) and request.method == 'POST':
        term = request.POST.get('term', '')
        customers = Customer.objects.filter(
            name__icontains=term
        ).values('id', 'name')
        customer_list = list(customers)
        return JsonResponse(customer_list, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = 'accounts/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 10


class VendorCreateView(LoginRequiredMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'accounts/vendor_form.html'
    success_url = reverse_lazy('vendor-list')


class VendorUpdateView(LoginRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'accounts/vendor_form.html'
    success_url = reverse_lazy('vendor-list')


class VendorDeleteView(LoginRequiredMixin, DeleteView):
    model = Vendor
    template_name = 'accounts/vendor_confirm_delete.html'
    success_url = reverse_lazy('vendor-list')


def is_admin(user):
    return user.is_authenticated and user.profile.role == 'AD'


@user_passes_test(is_admin)
def create_staff_member(request):
    """
    View to create a new staff member with auto-generated credentials
    """
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        telephone = request.POST.get('telephone')
        role = request.POST.get('role')
        status = request.POST.get('status')
        
        # Validate required fields
        if not all([username, email, first_name, last_name, role, status]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'accounts/create_staff_member.html', {
                'role_choices': ROLE_CHOICES,
                'status_choices': STATUS_CHOICES,
                'form_data': request.POST
            })
        
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/create_staff_member.html', {
                'role_choices': ROLE_CHOICES,
                'status_choices': STATUS_CHOICES,
                'form_data': request.POST
            })
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/create_staff_member.html', {
                'role_choices': ROLE_CHOICES,
                'status_choices': STATUS_CHOICES,
                'form_data': request.POST
            })
        
        try:
            # Generate a random password
            temp_password = get_random_string(12)
            
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=temp_password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Check if profile already exists (shouldn't for new user, but just in case)
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'telephone': telephone,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'status': status,
                    'role': role
                }
            )
            
            # If profile already existed, update it
            if not created:
                profile.telephone = telephone
                profile.email = email
                profile.first_name = first_name
                profile.last_name = last_name
                profile.status = status
                profile.role = role
                profile.save()
            
            # Send email with credentials
            subject = 'Your Staff Account Has Been Created'
            
            # Render HTML email template
            html_message = render_to_string('email/staff_created.html', {
                'staff_user': user,
                'temp_password': temp_password,
                'admin_name': request.user.get_full_name() or request.user.username,
                'login_url': request.build_absolute_uri('/accounts/login/')
            })
            
            # Create plain text version
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            messages.success(request, f'Staff member {username} created successfully. Temporary password sent to their email.')
            return redirect('profile_list')
            
        except IntegrityError as e:
            # Handle duplicate profile error specifically
            if 'accounts_profile.user_id' in str(e):
                # If user was created but profile failed, delete the user
                if User.objects.filter(username=username).exists():
                    User.objects.get(username=username).delete()
                messages.error(request, 'Error creating profile: This user already has a profile.')
            else:
                messages.error(request, f'Database error: {str(e)}')
            logger.error(f"IntegrityError creating staff member: {str(e)}")
            return render(request, 'accounts/create_staff_member.html', {
                'role_choices': ROLE_CHOICES,
                'status_choices': STATUS_CHOICES,
                'form_data': request.POST
            })
            
        except Exception as e:
            # If anything goes wrong, delete the user and show error
            if User.objects.filter(username=username).exists():
                User.objects.get(username=username).delete()
            logger.error(f"Error creating staff member: {str(e)}")
            messages.error(request, f'Error creating staff member: {str(e)}')
            return render(request, 'accounts/create_staff_member.html', {
                'role_choices': ROLE_CHOICES,
                'status_choices': STATUS_CHOICES,
                'form_data': request.POST
            })
    
    # GET request - show form
    return render(request, 'accounts/create_staff_member.html', {
        'role_choices': ROLE_CHOICES,
        'status_choices': STATUS_CHOICES
    })
    
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Check if user is admin
def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'AD'

@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def reset_staff_credentials(request, user_id):
    """
    View to reset staff credentials. Generates a new random password,
    updates the user account, and sends an email notification.
    """
    # Get the staff user or return 404
    staff_user = get_object_or_404(User, id=user_id)
    
    # Ensure we're not modifying a superuser (unless current user is also superuser)
    if staff_user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to reset credentials for superusers.')
        return redirect('staff_list')
    
    if request.method == 'POST':
        try:
            # Generate a secure random password
            new_password = get_random_string(14)  # Longer password for better security
            
            # Update the password
            staff_user.set_password(new_password)
            staff_user.save()
            
            # Prepare email content
            subject = 'Your Password Has Been Reset'
            
            # Render HTML email template
            html_message = render_to_string('email/password_reset.html', {
                'staff_user': staff_user,
                'new_password': new_password,
                'admin_name': request.user.get_full_name() or request.user.username,
            })
            
            # Create plain text version
            plain_message = strip_tags(html_message)
            
            # Send email with new credentials
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff_user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Log the action
            logger.info(f"Password reset for user {staff_user.username} by admin {request.user.username}")
            
            # Add success message
            messages.success(request, f'Password for {staff_user.username} has been reset successfully. The new password has been emailed to them.')
            
            # If request is AJAX, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Password for {staff_user.username} has been reset successfully.'
                })
                
            return redirect('staff_list')
            
        except Exception as e:
            # Log the error
            logger.error(f"Error resetting password for user {staff_user.id}: {str(e)}")
            
            # Add error message
            error_msg = f'Error resetting password: {str(e)}'
            messages.error(request, error_msg)
            
            # If request is AJAX, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                }, status=500)
                
            return redirect('staff_list')
    
    # GET request - show confirmation page
    context = {
        'staff_user': staff_user,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    }
    
    # If AJAX request, render a minimal template
    if context['is_ajax']:
        return render(request, 'accounts/confirm_reset_modal.html', context)
    
    return render(request, 'accounts/confirm_reset.html', context)