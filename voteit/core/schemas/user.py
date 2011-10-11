from urllib import quote

import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.core import VoteITMF as _
from voteit.core.validators import html_string_validator
from voteit.core.validators import deferred_unique_email_validator
from voteit.core.validators import password_validation
from voteit.core.validators import deferred_new_userid_validator
from voteit.core.validators import deferred_password_token_validator


@colander.deferred
def deferred_referer(node, kw):
    request = kw['request']
    return quote(request.GET.get('came_from', '/'))


def password_node():
    return colander.SchemaNode(colander.String(),
                               validator=colander.All(password_validation, html_string_validator,),
                        widget=deform.widget.CheckedPasswordWidget(size=20),
                        title=_('Password'))

def email_node():
    return colander.SchemaNode(colander.String(),
                               title=_(u"Email"),
                               validator=deferred_unique_email_validator,)

def first_name_node():
    return colander.SchemaNode(colander.String(),
                               title=_(u"First name"),
                               validator=html_string_validator,)
    
def last_name_node():
    return colander.SchemaNode(colander.String(),
                               title=_(u"Last name"),
                               missing=u"",
                               validator=html_string_validator,)

def came_from_node():
    return colander.SchemaNode(colander.String(),
                               widget = deform.widget.HiddenWidget(),
                               default=deferred_referer,)


@schema_factory('AddUserSchema')
class AddUserSchema(colander.Schema):
    """ Used for registration and regular add command. """
    userid = colander.SchemaNode(colander.String(),
                                 title = _(u"UserID"),
                                 description = _('userid_description',
                                                 default=u"Used as a nickname, in @-links and as a unique id. You can't change this later. Note that it's case sensitive!"),
                                 validator=deferred_new_userid_validator,)
    password = password_node()
    email = email_node()
    first_name = first_name_node()
    last_name = last_name_node()
    came_from = came_from_node()


@schema_factory('EditUserSchema')
class EditUserSchema(colander.Schema):
    """ Regular edit. """
    email = email_node()
    first_name = first_name_node()
    last_name = last_name_node()
    about_me = colander.SchemaNode(colander.String(),
        title = _(u"About me"),
        description = _(u"user_about_me_description",
                        default=u"Please note that anything you type here will be visible to all users in the same meeting as you."),
        widget = deform.widget.TextAreaWidget(rows=10, cols=60),
        missing=u"",
        validator=html_string_validator,)


@schema_factory('LoginSchema')
class LoginSchema(colander.Schema):
    userid = colander.SchemaNode(colander.String(),
                                 title=_(u"UserID or email address."))
    password = colander.SchemaNode(colander.String(),
                                   title=_('Password'),
                                   widget=deform.widget.PasswordWidget(size=20),)
    came_from = came_from_node()


@schema_factory('ChangePasswordSchema')
class ChangePasswordSchema(colander.Schema):
    password = password_node()


@schema_factory('RequestNewPasswordSchema')
class RequestNewPasswordSchema(colander.Schema):
    userid_or_email = colander.SchemaNode(colander.String(),
                                          title = _(u"UserID or email address."))


@schema_factory('TokenPasswordChangeSchema')
class TokenPasswordChangeSchema(colander.Schema):
    #FIXME: Implement captcha here to avoid bruteforce
    token = colander.SchemaNode(colander.String(),
                                validator = deferred_password_token_validator,
                                missing = u'',
                                widget = deform.widget.HiddenWidget(),)
    password = password_node()