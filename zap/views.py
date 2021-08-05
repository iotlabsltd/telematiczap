from rest_framework import status
from django.http.response import JsonResponse
from rest_framework.views import APIView
from rest_framework import authentication, permissions
from rest_framework.response import Response
from django.views.generic.edit import FormView
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
from .forms import UserRegisterForm, HomeForm
from django.urls import reverse_lazy
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from transformer.transform import transform
from rest_framework import filters
from .models import User, DataBefore, DataAfter, DataFormat, DataFormatClues
from .serializers import DataBeforeSerializer, DataAfterSerializer, DataFormatSerializer, DataFormatCluesSerializer
from django_filters.rest_framework import DjangoFilterBackend

class ApiEndpoint(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, OAuth2!')


class HomeFormView(FormView):
    template_name = 'home.html'
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
            transform(input_file=data_before_path, output_file=tmp_output_path, 
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


#        self.object = form.instance #form.save()
#        context = {'articles': Article.objects.all()}
#        data['html_articles'] = render_to_string(
#            'article/articles.html',
#            context
#        )
#        # NEXT LINE
#        data['form_is_valid'] = True
#        return JsonResponse(data)
        
#class HomeView(TemplateView):
#    template_name = 'home.html'
#
#    def get_context_data(self, **kwargs):
#        context = super().get_context_data(**kwargs)
#        context['user'] = self.request.user
#        context['title'] = 'Home'
#        return context
    

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


class UserLoginFormView(FormView):
    template_name = 'registration/login.html'
    form_class = UserRegisterForm
    success_url = '/'

    def form_valid(self, form):
        valid = super().form_valid(form)
        if valid:
            # Login the user, show message and redirect
            login(self.request, self.object)
            messages.success(self.request, "Login successful.")
            return redirect('/')
        else:
            # Show error
            messages.error(self.request, "Unsuccessful registration. Invalid information.")
            return valid


#THIS WORKS BUT IT'S UGLY
#def register(request):
#    if request.method == "POST":
#        form = UserRegisterForm(request.POST)
#        if form.is_valid():
#            user = form.save()
#            login(request, user)
#            messages.success(request, "Registration successful.")
#            return redirect("/")
#        else:
#            messages.error(request, "Unsuccessful registration. Invalid information.")
#    form = UserRegisterForm()
#    return render(request=request, template_name="registration/register.html", context={"register_form": form, 'title': 'Register'})
#
#class DatasetBeforeFormView(FormView):
#    template_name = 'data/upload-before.html'
#    form_class = DataBeforeForm
#    success_url = '/'
#
#    def form_valid(self, form):
#        form.save()
#        return super().form_valid(form)
#
#    def form_valid(self, form):
#        valid = super().form_valid(form)
#        if valid:
#            dataset = form.save()
#            messages.success(self.request, "Dataset uploaded.")
#            return redirect('/')
#        else:
#            messages.error(self.request, "Failed to submit the dataset.")
#            return valid
#
#class DataBeforeList(generics.ListAPIView):
#    """
#    View to list all users in the system.
#
#    * Requires token authentication.
#    * Only admin users are able to access this view.
#    """
#    authentication_classes = [authentication.TokenAuthentication]
#    #permission_classes = [permissions.IsAdminUser]
#
#    def get(self, request, format=None):
#        """
#        Return a list of all users.
#        """
#        usernames = [user.username for user in User.objects.all()]
#        return Response(usernames)


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
