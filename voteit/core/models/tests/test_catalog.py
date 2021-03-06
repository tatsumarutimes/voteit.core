import unittest
from calendar import timegm

from arche.utils import utcnow
from pyramid import testing

from voteit.core import security
from voteit.core.bootstrap import bootstrap_voteit
from voteit.core.models.arche_compat import createContent
from voteit.core.testing_helpers import bootstrap_and_fixture


class CatalogIndexTests(unittest.TestCase):
    """ Make sure indexes work as expected. """

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.include('arche.testing')
        self.config.include('arche.models.catalog')
        self.config.include('voteit.core.models.meeting')
        self.config.include('voteit.core.models.site')
        self.config.include('voteit.core.models.agenda_templates')
        self.config.include('voteit.core.models.user')
        self.config.include('voteit.core.models.users')
        self.config.include('voteit.core.models.catalog') 
        self.root = bootstrap_voteit(echo=False)
        self.query = self.root.catalog.query
        self.search = self.root.catalog.search
        self.get_metadata = self.root.document_map.get_metadata
        self.config.include('voteit.core.testing_helpers.register_workflows')
 
    def tearDown(self):
        testing.tearDown()
 
    def _add_mock_meeting(self):
        from voteit.core.models.meeting import Meeting
        obj = Meeting(title = 'Testing catalog',
                      description = 'To check that everything works as expected.',
                      uid = 'simple_uid', creators = ['demo_userid'])
        obj.add_groups('admin', (security.ROLE_ADMIN, security.ROLE_MODERATOR,), event = False)
        self.root['meeting'] = obj
        return obj
 
    def test_workflow_state(self):
        self._add_mock_meeting()
        self.assertEqual(self.query("workflow_state == 'upcoming'")[0], 1)
 
    def test_allowed_to_view(self):
        self.config.include('arche.testing.setup_auth')
        obj = self._add_mock_meeting()
        #Owners are not allowed to view meetings. It's exclusive for Admins / Moderators right now
        self.assertEqual(self.query("allowed_to_view in any('404',) and path == '/meeting'")[0], 0)
        self.assertEqual(self.query("allowed_to_view in any('role:Viewer',) and path == '/meeting'")[0], 1)
        self.assertEqual(self.query("allowed_to_view in any('role:Administrator',) and path == '/meeting'")[0], 1)
        self.assertEqual(self.query("allowed_to_view in any('role:Moderator',) and path == '/meeting'")[0], 1)
 
    def test_view_meeting_userids(self):
        self.config.include('arche.testing.setup_auth')
        #Must add a user to users folder too, otherwise the find_authorized_userids won't accept them as valid
        self.root['users']['demo_userid'] = createContent('User')
        obj = self._add_mock_meeting()
        self.assertEqual(self.search(view_meeting_userids = 'demo_userid')[0], 1)
 
    def test_start_time(self):
        obj = self._add_mock_meeting()
        now = utcnow()
        now_unix = timegm(now.timetuple())
        #Shouldn't return anything
        self.assertEqual(self.query("start_time == %s and path == '/meeting'" % now_unix)[0], 0)
        qy = ("%s < start_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
        self.assertEqual(self.query(qy)[0], 0)
        #So let's set it and return stuff
        obj.update(start_time = now)         
        self.assertEqual(self.query("start_time == %s and path == '/meeting'" % now_unix)[0], 1)
        qy = ("%s < start_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
        self.assertEqual(self.query(qy)[0], 1)
 
    def test_end_time(self):
        obj = self._add_mock_meeting()
        now = utcnow()
        now_unix = timegm(now.timetuple())
        obj.update(end_time = now)
        self.assertEqual(self.query("end_time == %s and path == '/meeting'" % now_unix)[0], 1)
        qy = ("%s < end_time < %s and path == '/meeting'" % (now_unix-1, now_unix+1))
        self.assertEqual(self.query(qy)[0], 1)

    def test_additions_to_searchable_text(self):
        meeting = self._add_mock_meeting()
        meeting.update(body = "<p>Jane Doe</p>")
        self.assertEqual(self.search(searchable_text = 'Jane Doe')[0], 1)


class CatalogSubscriberTests(unittest.TestCase):
 
    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())
        self.config.include('arche.models.catalog')
        self.config.include('voteit.core.models.catalog')
        self.config.include('voteit.core.models.catalog')
 
    def tearDown(self):
        testing.tearDown()
 
    def _fixture(self):
        return bootstrap_and_fixture(self.config)
 
    @property
    def _ai(self):
        """ Has metadata enabled """
        from voteit.core.models.agenda_item import AgendaItem
        return AgendaItem
 
    # def _metadata_for_query(self, root, **kw):
    #     from voteit.core.models.catalog import metadata_for_query
    #     return metadata_for_query(root, **kw)
     
    def test_object_added_catalog(self):
        root = self._fixture()
        text = 'New object'
        root['new_obj'] = self._ai(title = text)
        self.assertEqual(root.catalog.search(title = text)[0], 1)
     
    # def test_object_added_metadata(self):
    #     root = self._fixture()
    #     text = 'New object'
    #     root['new_obj'] = self._ai(title = text)
    #     metadata = self._metadata_for_query(root, title = text)
    #     self.assertEqual(metadata[0]['title'], text)
 
    def test_object_updated_wf_changed_catalog(self):
        root = self._fixture()
        request = testing.DummyRequest()
        text = 'New object'
        root['new_obj'] = self._ai(title = text)
        root['new_obj'].set_workflow_state(request, 'upcoming')
        self.assertEqual(root.catalog.search(title = text, workflow_state = 'upcoming')[0], 1)

    def test_object_updated_from_appstruct_catalog(self):
        root = self._fixture()
        ai = self._ai(title = 'New object')
        root['new_obj'] = ai
        ai.set_field_appstruct({'title': 'New title'})
        self.assertEqual(root.catalog.search(title = 'New title')[0], 1)
 
    def test_object_deleted_from_catalog(self):
        root = self._fixture()
        ai = self._ai(title = 'New object')
        root['new_obj'] = ai
        #Just to make sure
        self.assertEqual(root.catalog.search(uid = ai.uid)[0], 1)
        del root['new_obj']
        self.assertEqual(root.catalog.search(uid = ai.uid)[0], 0)
 
    # def test_object_deleted_from_metadata(self):
    #     root = self._fixture()
    #     ai = self._ai(title = 'New object')
    #     root['new_obj'] = ai
    #     #Just to make sure
    #     self.failUnless(self._metadata_for_query(root, uid = ai.uid))
    #     del root['new_obj']
    #     self.failIf(self._metadata_for_query(root, uid = ai.uid))
 
    def test_update_contained_in_ai(self):
        self.config.include('arche.testing.setup_auth')
        self.config.include('arche.testing')
        self.config.include('voteit.core.models.meeting')
        self.config.include('voteit.core.models.discussion_post')
        from voteit.core.models.discussion_post import DiscussionPost
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.user import User
        root = self._fixture()
        root['users']['john'] = User()
        root['m'] = Meeting()
        root['m'].add_groups('john', [security.ROLE_VIEWER])
        root['m']['ai'] = ai = self._ai(title = 'New object')
        ai['dp'] = dp = DiscussionPost()
        #To make sure dp got catalogued
        self.assertEqual(root.catalog.search(uid = dp.uid)[0], 1)
        #The discussion post shouldn't be visible now, since the ai is private
        self.assertEqual(root.catalog.search(uid = dp.uid, allowed_to_view = [security.ROLE_VIEWER])[0], 0)
        #When the ai is made upcoming, it should be visible
        security.unrestricted_wf_transition_to(ai, 'upcoming')
        self.assertEqual(root.catalog.search(uid = dp.uid, allowed_to_view = [security.ROLE_VIEWER])[0], 1)
