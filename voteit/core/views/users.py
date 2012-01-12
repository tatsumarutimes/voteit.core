import urllib

from pyramid.view import view_config
from deform import Form
from deform.exception import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import Forbidden
from pyramid.url import resource_url
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.security import remember
from pyramid.security import forget
from pyramid.renderers import render
from betahaus.pyracont.factories import createContent
from betahaus.pyracont.factories import createSchema

from voteit.core import VoteITMF as _
from voteit.core.models.interfaces import ISiteRoot
from voteit.core.models.interfaces import IUser
from voteit.core.models.interfaces import IUsers
from voteit.core.views.api import APIView
from voteit.core.security import CHANGE_PASSWORD
from voteit.core.security import VIEW
from voteit.core.models.schemas import add_csrf_token
from voteit.core.models.schemas import button_add
from voteit.core.models.schemas import button_cancel
from voteit.core.models.schemas import button_change
from voteit.core.models.schemas import button_login
from voteit.core.models.schemas import button_register
from voteit.core.models.schemas import button_request
from voteit.core.models.schemas import button_update
from voteit.core.views.userinfo import user_info_view
from voteit.core.views.base_view import BaseView
from voteit.core.views.base_edit import BaseEdit


DEFAULT_TEMPLATE = "templates/base_edit.pt"
LOGIN_REGISTER_TPL = "templates/login_register.pt"


class UsersFormView(BaseEdit):
    """ View class for adding, editing or deleting users.
        It also handles users own login and registration.
    """

    @view_config(context=IUsers, name="add", renderer=DEFAULT_TEMPLATE)
    def add_form(self):
        post = self.request.POST
        if 'cancel' in post:
            self.api.flash_messages.add(_(u"Canceled"))
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        schema = createSchema('AddUserSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=(button_add, button_cancel))
        self.api.register_form_resources(form)

        if 'add' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            #Userid and name should be consistent
            name = appstruct['userid']
            del appstruct['userid']
            
            #creators takes care of setting the role owner as well as adding it to creators attr.
            obj = createContent('User', creators=[name], **appstruct)
            self.context[name] = obj

            self.api.flash_messages.add(_(u"Successfully added"))

            url = resource_url(self.context, self.request)            
            return HTTPFound(location=url)

        #No action - Render add form
        msg = _(u"Add new user")
        self.api.flash_messages.add(msg, close_button=False)
        self.response['form'] = form.render()
        return self.response

    @view_config(context=IUser, name="change_password", renderer=DEFAULT_TEMPLATE, permission=CHANGE_PASSWORD)
    def password_form(self):
        schema = createSchema('ChangePasswordSchema').bind(context=self.context, request=self.request)
        add_csrf_token(self.context, self.request, schema)

        form = Form(schema, buttons=(button_update, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'update' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            self.context.set_password(appstruct['password'])
            url = resource_url(self.context, self.request)
            
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.context, self.request)
            return HTTPFound(location=url)

        #No action - Render edit form
        self.response['form'] = form.render()
        return self.response

    @view_config(context=IUser, name="token_pw", renderer=DEFAULT_TEMPLATE, permission=NO_PERMISSION_REQUIRED)
    def token_password_change(self):
        schema = createSchema('TokenPasswordChangeSchema').bind(context=self.context, request=self.request)

        form = Form(schema, buttons=(button_change, button_cancel))
        self.api.register_form_resources(form)

        post = self.request.POST
        if 'change' in post:
            controls = post.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            self.context.remove_password_token()
            self.context.set_password(appstruct['password'])
            self.api.flash_messages.add(_(u"Password set. You may login now."))
            url = "%s@@login" % resource_url(self.api.root, self.request)
            return HTTPFound(location=url)

        if 'cancel' in post:
            url = resource_url(self.api.root, self.request)
            return HTTPFound(location=url)

        #Fetch token from get request
        token = self.request.GET.get('token', None)
        if token is None:
            msg = _(u"Invalid security token. Did you click the link in your email?")
            self.api.flash_messages.add(msg, type="error")
            url = resource_url(self.api.root, self.request)
            return HTTPFound(location=url)

        #Everything seems okay. Render form
        appstruct = dict(token = token)
        self.response['form'] = form.render(appstruct=appstruct)
        return self.response

    @view_config(context=ISiteRoot, name="register", renderer=LOGIN_REGISTER_TPL)
    @view_config(context=ISiteRoot, name='login', renderer=LOGIN_REGISTER_TPL)
    def login_or_register(self):
        users = self.api.root.users
        
        login_schema = createSchema('LoginSchema').bind(context=self.context, request=self.request)        
        register_schema = createSchema('AddUserSchema').bind(context=self.context, request=self.request)

        login_form = Form(login_schema, buttons=(button_login,))
        reg_form = Form(register_schema, buttons=(button_register,))

        self.api.register_form_resources(login_form)
        self.api.register_form_resources(reg_form)

        appstruct = {}

        POST = self.request.POST
    
        #Handle submitted information
        if 'login' in POST:
            controls = POST.items()
    
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = login_form.validate(controls)
            except ValidationFailure, e:
                self.response['login_form'] = e.render()
                return self.response
            
            userid = appstruct['userid']
            password = appstruct['password']
            came_from = urllib.unquote(appstruct['came_from'])
    
            #userid here can be either an email address or a login name
            if '@' in userid:
                #assume email
                user = users.get_user_by_email(userid)
            else:
                user = users.get(userid)
            
            if IUser.providedBy(user):
                pw_field = user.get_custom_field('password')
                if pw_field.check_input(password):
                    headers = remember(self.request, user.__name__)
                    url = resource_url(self.context, self.request)
                    if came_from:
                        url = came_from
                    return HTTPFound(location = url,
                                     headers = headers)
            self.response['api'].flash_messages.add(_('Login failed.'), type='error')

        if 'register' in POST:
            controls = POST.items()
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = reg_form.validate(controls)
            except ValidationFailure, e:
                self.response['reg_form'] = e.render()
                return self.response
            
            #Userid and name should be consistent - and not stored
            name = appstruct['userid']
            del appstruct['userid']

            #Came from should not be stored either
            came_from = urllib.unquote(appstruct['came_from'])
            if came_from:
                url = came_from
            else:
                url = "%slogin" % resource_url(self.context, self.request)
            del appstruct['came_from']

            obj = createContent('User', creators=[name], **appstruct)
            self.context.users[name] = obj
            headers = remember(self.request, name)  # login user

            return HTTPFound(location=url, headers=headers)

        #Set came from in form
        came_from = self.request.GET.get('came_from', None)
        if came_from:
            appstruct['came_from'] = came_from

        #Render forms
        self.response['login_form'] = login_form.render(appstruct)
        self.response['reg_form'] = reg_form.render(appstruct)
        return self.response
        
        
    @view_config(context=ISiteRoot, name='cso', renderer=DEFAULT_TEMPLATE, 
                 permission=NO_PERMISSION_REQUIRED)
    def cloud_sign_on(self):
        if 'token' in self.request.POST:
            token = self.request.POST['token']
            
            import urllib2
            import json

            data = {'format': 'json', 'token': token}
            url = self.request.application_url + "/velruse/auth_info?" + urllib.urlencode(data)
            stream = urllib2.urlopen(url)
            response = json.loads(stream.read())
            oauth_token = response['credentials']['oauthAccessToken']
            
            user = self.context.users.get_user_by_oauth_token(oauth_token)
            
            if user:
                if IUser.providedBy(user):
                    headers = remember(self.request, user.__name__)
                    url = resource_url(self.context, self.request)
                    return HTTPFound(location = url,
                                     headers = headers)
            else: # User does not have an account
                #FIXME: this ONLY works with Facebook right now and expects 
                # that the username is not already in use.
                # In the future the user should be presented with a form 
                # prefilled with data from the provider. 
                # The username should already be checked for duplicates and
                # an alternatvie proposed.
                name = response['profile']['preferredUsername']
                first_name = response['profile']['name']['givenName']
                last_name = response['profile']['name']['familyName']
                appstruct = {'oauthAccessToken': oauth_token, 
                             'first_name': first_name,
                             'last_name': last_name,}
                obj = createContent('User', creators=[name], **appstruct)
                self.context.users[name] = obj
                headers = remember(self.request, name)  # login user
                url = "%slogin" % resource_url(self.context, self.request)

                return HTTPFound(location=url, headers=headers)
                
            
        raise Forbidden(_("Unable to Authenticate you using OpenID"))


    @view_config(context=ISiteRoot, name='request_password',
                 renderer=DEFAULT_TEMPLATE, permission=NO_PERMISSION_REQUIRED)
    def request_password(self):        
        schema = createSchema('RequestNewPasswordSchema').bind(context=self.context, request=self.request)
        form = Form(schema, buttons=(button_request, button_cancel))
        self.api.register_form_resources(form)
    
        #Handle submitted information
        if 'request' in self.request.POST:
            controls = self.request.POST.items()
    
            try:
                #appstruct is deforms convention. It will be the submitted data in a dict.
                appstruct = form.validate(controls)
            except ValidationFailure, e:
                self.response['form'] = e.render()
                return self.response
            
            userid_or_email = appstruct['userid_or_email']
    
            #userid here can be either an email address or a login name
            if '@' in userid_or_email:
                #assume email
                user = self.context['users'].get_user_by_email(userid_or_email)
            else:
                user = self.context['users'].get(userid_or_email)
            
            if IUser.providedBy(user):
                user.new_request_password_token(self.request)
                self.api.flash_messages.add(_('Email sent.'))
                url = resource_url(self.api.root, self.request)
                return HTTPFound(location = url)
    
            self.api.flash_messages.add(_('Username or email not found.'), type='error')
        
        if 'cancel' in self.request.POST:
            url = resource_url(self.api.root, self.request)
            return HTTPFound(location = url)
    
        #Render form
        self.response['form'] = form.render()
        return self.response
        
        
    @view_config(context=ISiteRoot, name='logout')
    def logout(self):
        headers = forget(self.request)
        return HTTPFound(location = resource_url(self.context, self.request),
                         headers = headers)


class UsersView(BaseView):
    """ Any regular view action without forms. """

    @view_config(context=IUsers, renderer='templates/list_users.pt', permission=VIEW)
    def list_users(self):
        return self.response

    @view_config(context=IUser, renderer='templates/user.pt', permission=VIEW)
    def view_user(self):
        self.response['user_info'] = user_info_view(self.context, self.request, info_userid=self.context.userid)
        return self.response
