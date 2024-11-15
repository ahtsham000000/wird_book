from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from .forms import AdminLoginForm, EditPhoneNumberForm, AssignAdminForm
from myapp.models import PhoneNumber, Token, CommunityMember
from django.db import transaction, IntegrityError


class AdminLoginView(View):
    template_name = 'custom_admin/login.html'
    form_class = AdminLoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('custom_admin:dashboard')
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                if user.is_staff:
                    login(request, user)
                    return redirect('custom_admin:dashboard')
                form.add_error(None, 'You do not have admin privileges.')
            else:
                form.add_error(None, 'Invalid username or password.')
        return render(request, self.template_name, {'form': form})


class AdminLogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('custom_admin:login')

# custom_admin/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import Q
from .forms import AdminLoginForm, EditPhoneNumberForm, AssignAdminForm, EditMemberStatusForm
from myapp.models import PhoneNumber, Token, CommunityMember, NoticeboardPost, Question, Answer

class AdminDashboardView(LoginRequiredMixin, View):
    template_name = 'custom_admin/dashboard.html'

    def get(self, request):
        selected_community = request.GET.get('community', None)
        communities = CommunityMember.COMMUNITY_CHOICES

        # Get community data for display
        community_data = [
            {'id': value, 'name': name, 'count': CommunityMember.objects.filter(community=value).count()}
            for value, name in communities
        ]

        context = {
            'communities': communities,
            'community_data': community_data,
            'selected_community': selected_community,
        }

        if selected_community:
            # Get members of the selected community
            community_members = CommunityMember.objects.filter(community=selected_community).select_related('phone_number')
            # Separate accepted and pending/rejected members
            accepted_members = community_members.filter(status='accepted')
            pending_members = community_members.exclude(status='accepted')

            # Pagination for accepted members
            accepted_page_obj = Paginator(accepted_members, 10).get_page(request.GET.get('accepted_page'))
            # Pagination for pending/rejected members
            pending_page_obj = Paginator(pending_members, 10).get_page(request.GET.get('pending_page'))

            context.update({
                'accepted_members': accepted_page_obj.object_list,
                'pending_members': pending_page_obj.object_list,
                'accepted_page_obj': accepted_page_obj,
                'pending_page_obj': pending_page_obj,
            })

        return render(request, self.template_name, context)



class ViewPhoneNumberView(LoginRequiredMixin, View):
    template_name = 'custom_admin/view_phone.html'

    def get(self, request, number):
        phone = get_object_or_404(PhoneNumber, number=number)
        token = Token.objects.filter(phone_number=phone).first()
        community_members = phone.community_members.all()

        # Fetch posts, questions, and answers associated with this phone number
        noticeboard_posts = NoticeboardPost.objects.filter(created_by=phone).order_by('-created_at')
        questions = Question.objects.filter(created_by=phone).order_by('-created_at')
        answers = Answer.objects.filter(created_by=phone).order_by('-created_at')

        context = {
            'phone': phone,
            'token': token,
            'community_members': community_members,
            'noticeboard_posts': noticeboard_posts,
            'questions': questions,
            'answers': answers,
        }
        return render(request, self.template_name, context)



class AssignAdminView(LoginRequiredMixin, View):
    template_name = 'custom_admin/assign_admin.html'
    form_class = AssignAdminForm

    def get(self, request, number, community_id):
        phone = get_object_or_404(PhoneNumber, number=number)
        community_member = get_object_or_404(CommunityMember, phone_number=phone, community=community_id)
        form = self.form_class(instance=community_member)
        return render(request, self.template_name, {'form': form, 'phone': phone, 'community_member': community_member})

    def post(self, request, number, community_id):
        phone = get_object_or_404(PhoneNumber, number=number)
        community_member = get_object_or_404(CommunityMember, phone_number=phone, community=community_id)
        form = self.form_class(request.POST, instance=community_member)

        if form.is_valid():
            try:
                with transaction.atomic():
                    if form.cleaned_data['role'] == 'admin':
                        # Demote other admins in the same community
                        CommunityMember.objects.filter(community=community_id, role='admin').exclude(id=community_member.id).update(role='user')
                    form.save()

                    # Update the role in the PhoneNumber instance
                    phone.role = form.cleaned_data['role']
                    phone.save()

                    messages.success(request, f"Role updated to '{form.cleaned_data['role']}' for {phone.number} in {community_member.get_community_display()}.")
                    return redirect('custom_admin:dashboard')
            except IntegrityError:
                form.add_error(None, 'An error occurred while assigning the admin role. Please try again.')

        return render(request, self.template_name, {'form': form, 'phone': phone, 'community_member': community_member})



class DeletePhoneNumberView(LoginRequiredMixin, View):
    def post(self, request, number):
        phone = PhoneNumber.objects.filter(number=number).first()
        if phone:
            phone.delete()
            messages.success(request, f'Phone number {number} has been deleted.')
        else:
            messages.error(request, f'Phone number {number} does not exist.')
        return redirect('custom_admin:dashboard')


class EditPhoneNumberView(LoginRequiredMixin, View):
    template_name = 'custom_admin/edit_phone.html'

    def get(self, request, number):
        phone = get_object_or_404(PhoneNumber, number=number)
        form = EditPhoneNumberForm(instance=phone)
        return render(request, self.template_name, {'form': form, 'phone': phone})

    def post(self, request, number):
        phone = get_object_or_404(PhoneNumber, number=number)
        form = EditPhoneNumberForm(request.POST, instance=phone)
        if form.is_valid():
            form.save()
            messages.success(request, f'Phone number {phone.number} has been updated.')
            return redirect('custom_admin:dashboard')
        return render(request, self.template_name, {'form': form, 'phone': phone})


class EditMemberStatusView(LoginRequiredMixin, View):
    template_name = 'custom_admin/edit_member_status.html'

    def get(self, request, member_id):
        member = get_object_or_404(CommunityMember, id=member_id)
        form = EditMemberStatusForm(instance=member)
        return render(request, self.template_name, {'form': form, 'member': member})

    def post(self, request, member_id):
        member = get_object_or_404(CommunityMember, id=member_id)
        form = EditMemberStatusForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Status updated to "{member.get_status_display}" for {member.phone_number.number} in {member.get_community_display()}.')
            return redirect('custom_admin:dashboard')
        return render(request, self.template_name, {'form': form, 'member': member})
