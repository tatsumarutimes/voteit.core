import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.core.testing_helpers import register_security_policies
from voteit.core.testing_helpers import register_catalog


class SearchViewTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.core.views.api import APIView
        return APIView

    def test_authn_policy(self):
        self.config.testing_securitypolicy('dummy')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.authn_policy)

    def test_authz_policy(self):
        self.config.testing_securitypolicy('dummy')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.authz_policy)

    def test_dt_util(self):
        self.config.registry.settings['default_timezone_name'] = 'Europe/Stockholm'
        self.config.include('voteit.core.models.date_time_util')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.dt_util)

    def test_user_profile(self):
        root = bootstrap_and_fixture(self.config)
        self.config.testing_securitypolicy('admin')
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        self.assertTrue(obj.user_profile)

    def test_flash_messages(self):
        self.config.include('voteit.core.models.flash_messages')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertTrue(obj.flash_messages)

    def test_render_flash_messages(self):
        self.config.include('voteit.core.models.flash_messages')
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        obj.flash_messages.add('Hello world')
        res = obj.render_flash_messages()
        self.failUnless('Hello world' in res)

    def test_show_moderator_actions(self):
        #FIXME: We still need a functional test for this
        root = bootstrap_and_fixture(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        self.assertTrue(obj.show_moderator_actions)

    def test_localizer(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        from pyramid.i18n import Localizer
        self.assertIsInstance(obj.localizer, Localizer)

    def test_translate(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        from pyramid.i18n import TranslationString
        dummy_ts = TranslationString("Hello")
        obj = self._cut(context, request)
        res = obj.translate(dummy_ts)
        self.assertIsInstance(res, unicode)
        self.assertNotIsInstance(res, TranslationString)

    def test_pluralize(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertEqual(obj.pluralize('Singular', 'Plural', 1), 'Singular')
        self.assertEqual(obj.pluralize('Singular', 'Plural', 2), 'Plural')

    def test_context_unread(self):
        register_catalog(self.config)
        self.config.testing_securitypolicy('admin', permissive = True)
        root = bootstrap_and_fixture(self.config)
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.discussion_post import DiscussionPost
        root['m'] = Meeting()
        ai = root['m']['ai'] = AgendaItem()
        ai['d1'] = DiscussionPost()
        ai['d2'] = DiscussionPost()
        request = testing.DummyRequest()
        obj = self._cut(ai, request)
        self.assertEqual(len(obj.context_unread), 2)

    def test_register_form_resources(self):
        import colander
        import deform
        class DummySchema(colander.Schema):
            dummy = colander.SchemaNode(colander.String())
        dummy_form = deform.Form(DummySchema())

        from fanstatic import get_needed
        from fanstatic import init_needed
        from fanstatic import NeededResources
        init_needed() #Otherwise fanstatic won't get a proper needed resrouces object.
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        obj.register_form_resources(dummy_form)
        needed_resources = get_needed()
        self.assertIsInstance(needed_resources, NeededResources)
        filenames = [x.filename for x in needed_resources.resources()]
        #Note: Can be any filename registered by VoteIT. Just change it if this test fails :)
        self.assertIn('deform.css', filenames)

    def test_tstring(self):
        from pyramid.i18n import TranslationString
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertIsInstance(obj.tstring('Hello'), TranslationString)

    def test_get_user(self):
        root = bootstrap_and_fixture(self.config)
        request = testing.DummyRequest()
        obj = self._cut(root, request)
        self.failIf(hasattr(request, '_user_lookup_cache'))
        user = obj.get_user('admin')
        from voteit.core.models.interfaces import IUser
        self.failUnless(IUser.providedBy(user))
        self.assertEqual(user, request._user_lookup_cache['admin'])

    def test_get_meeting_outside_meeting(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        obj = self._cut(context, request)
        self.assertEqual(obj.meeting, None)

    def test_get_meeting_inside_meeting(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        self.assertEqual(obj.meeting, meeting)

    def test_meeting_state(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        self.assertEqual(obj.meeting_state, u'upcoming')

    def test_meeting_url(self):
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        meeting = root['m'] = Meeting()
        request = testing.DummyRequest()
        obj = self._cut(meeting, request)
        #example.com is from Pyramids testing env
        self.assertEqual(obj.meeting_url, 'http://example.com/m/')

#    def get_moderator_actions
#    def get_time_created
#    def get_userinfo_url
#    def get_creators_info
#    def get_poll_state_info
#    def context_has_permission
#    def context_effective_principals
#    def is_brain_unread
#    def get_restricted_content
#
#    def search_catalog
#
#    def resolve_catalog_docid
#
#    def get_metadata_for_query
#    def get_content_factory
#
#    def content_types_add_perm
#
#    def get_schema_name
#
#    def render_view_group
#
#    def render_single_view_component



#FIXME: Write more tests :)