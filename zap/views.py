from django.views.generic.edit import CreateView
from rest_framework import status
from django.http.response import JsonResponse
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.response import Response
from django.views.generic import View, FormView
from oauth2_provider.views.generic import ProtectedResourceView
from .models import Message
from .forms import ContactForm
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework import generics, permissions, serializers
from django.contrib.auth.models import Group
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope
from django.views.generic.base import TemplateView
from .forms import HomeForm, UserRegisterForm, UserLoginForm
from django.urls import reverse_lazy
from rest_framework.permissions import IsAuthenticated
from transformer import TelematicZapTransformer
from rest_framework import filters
from .models import User, DataBefore, DataAfter, DataFormat, DataFormatClues
from .serializers import DataBeforeSerializer, DataAfterSerializer, DataFormatSerializer, DataFormatCluesSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.views import LoginView

class ApiEndpoint(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, OAuth2!')


class HomeFormView(FormView):
    template_name = 'index.html'
    form_class = HomeForm
    success_url = '/'

    def form_valid(self, form):
        print('transform!')
        valid = super().form_valid(form)
        if valid:
            # get data before and format
            data_before_path = form.files['data_before'].temporary_file_path()
            data_format_path = form.files['data_format'].temporary_file_path()
            # get path and format type
            data_format_type = data_format_path.split('.')[-1]
            tmp_output_filename = 'data_after.'+data_format_type
            tmp_output_path = '/tmp/'+tmp_output_filename
            # transform
            model = TelematicZapTransformer()
            model.transform_from_file(
                input_file=data_before_path, output_file=tmp_output_path, 
                output_example_file=data_format_path, limit_rows=100)
            # get data after
            with open(tmp_output_path, 'r') as f:
                file_data = f.read()
            # choose content type of response based on file type
            filetype = data_format_type.lower()
            if filetype == 'csv': content_type = 'text/csv'
            elif filetype == 'xls': content_type = 'application/vnd.ms-excel'
            elif filetype == 'xlsx': content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif filetype == 'json': content_type = 'application/json'
            else: content_type = 'application/octet-stream'
            # create response with file
            response = HttpResponse(file_data, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename={tmp_output_filename}'
            # return response
            return response
        else:
            return valid


class DashboardFormView(CreateView):  # ProtectedResourceView
    template_name = 'index.html'
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset1 = DataBefore.objects.filter(user=request.user)
        queryset2 = DataFormat.objects.filter(user=request.user)
        queryset3 = DataAfter.objects.filter(user=request.user)
        return render(request, self.template_name, {
            'queryset1': queryset1,
            'queryset2': queryset2,
            'queryset3': queryset3,
        })

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            if 'databefore' in request.POST:
                messages.success(request, 'Your dataset has been uploaded.')
                pass
                ## do what ever you want to do for first function ####
            if 'dataformat' in request.POST:
                messages.success(request, 'Your format has been uploaded.')
                pass
            if 'dataafter' in request.POST:
                messages.success(
                    request, 'Zap! Your dataset has been transformed!')
                pass
            ## do what ever you want to do for second function ####
            ## return def post###
        queryset1 = DataBefore.objects.filter(user=request.user)
        queryset2 = DataFormat.objects.filter(user=request.user)
        queryset3 = DataAfter.objects.filter(user=request.user)
        return render(request, self.template_name, {
            'queryset1': queryset1,
            'queryset2': queryset2,
            'queryset3': queryset3,
        })


class ContactFormView(FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = '/contact'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']
        message = Message(email=email, message=message)
        message.save()
        messages.success(self.request, 'Message received 👽')
        return super().form_valid(form)


class RegisterFormView(FormView):
    template_name = 'registration/signup.html'
    form_class = UserRegisterForm
    success_url = '/'

    def form_valid(self, form):
        valid = super().form_valid(form)
        if valid:
            user = form.save()
            login(self.request, user)
            messages.success(self.request, "Registration successful.")
            return redirect('/')
        else:
            messages.error(self.request, "Unsuccessful registration. Invalid information.")
            return valid


class LoginFormView(LoginView):
    template_name = 'registration/login.html'
    form_class = UserLoginForm


class IsOwnerFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(user=request.user)
class AuthenticatedListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [IsOwnerFilterBackend, DjangoFilterBackend]

    def perform_create(self, serializer, **kwargs):
        serializer.save(user=self.request.user, **kwargs)

class AuthenticatedRUDView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [IsOwnerFilterBackend, DjangoFilterBackend]


class DataBeforeList(AuthenticatedListCreateView):
    queryset = DataBefore.objects.all()
    serializer_class = DataBeforeSerializer

class DataBeforeRUD(AuthenticatedRUDView):
    queryset = DataBefore.objects.all()
    serializer_class = DataBeforeSerializer

class DataFormatList(AuthenticatedListCreateView):
    queryset = DataFormat.objects.all()
    serializer_class = DataFormatSerializer

class DataFormatRUD(AuthenticatedRUDView):
    queryset = DataFormat.objects.all()
    serializer_class = DataFormatSerializer

class DataAfterList(AuthenticatedListCreateView):
    queryset = DataAfter.objects.all()
    serializer_class = DataAfterSerializer

class DataAfterRUD(AuthenticatedRUDView):
    queryset = DataAfter.objects.all()
    serializer_class = DataAfterSerializer
