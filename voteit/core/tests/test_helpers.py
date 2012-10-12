# -*- coding: utf-8 -*-

import unittest

from pyramid import testing

from voteit.core.testing_helpers import bootstrap_and_fixture


class AtUseridLinkTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import at_userid_link
        return at_userid_link
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_function(self):
        from voteit.core.interfaces import IWorkflowStateChange
        value = self._fut('@admin', self._fixture())
        self.assertIn('/m/_userinfo?userid=admin', value)


class GenerateSlugTests(unittest.TestCase):
    
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request = request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import generate_slug
        return generate_slug
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        from voteit.core.models.proposal import Proposal
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_unique(self):
        context = self._fixture()
        value = self._fut(context, u'o1')
        self.assertIn(u'o1', value)
        
    def test_same(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal 
        context['o1'] = Proposal()
        value = self._fut(context, u'o1')
        self.assertIn(u'o1-1', value)
        
    def test_cant_find_unique(self):
        context = self._fixture()
        from voteit.core.models.proposal import Proposal
        context[u'o1'] = Proposal()
        for i in range(1, 101):
            context[u'o1-%s' % i] = Proposal()
        self.assertRaises(KeyError, self._fut, context, u'o1')
        

class Tags2linksTests(unittest.TestCase):
    
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request = self.request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import tags2links
        return tags2links
        
    def _fixture(self):
        from voteit.core.models.agenda_item import AgendaItem
        from voteit.core.models.meeting import Meeting
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        return ai

    def test_function(self):
        value = self._fut(u'#åäöÅÄÖ', self._fixture(), self.request)
        self.assertIn(u'/m/ai/?tag=%C3%A5%C3%A4%C3%B6%C3%85%C3%84%C3%96', value)

class StripAndTruncateTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.core.helpers import strip_and_truncate
        return strip_and_truncate

    def test_strip_and_truncate(self):
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris at enim nec nunc facilisis semper. Sed vel magna sit amet augue aliquet rhoncus metus."
        truncated = self._fut(text, 100)
        self.assertEqual(truncated, 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris at enim nec nunc facilisis semper. S&lt;...&gt;') 


class TruncateTests(unittest.TestCase):
        
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def test_truncate_long(self):
        
        text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
               u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
               u"consectetur adipiscing elit. In hac habitasse platea dictumst. " \
               u"Sed sit amet tortor at nisl malesuada tristique. Nulla faucibus " \
               u"egestas felis, at ullamcorper arcu sollicitudin amet."
                
        truncated_text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
                         u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
                         u"consectetur adipiscing elit. In hac habitasse platea dictumst. " \
                         u"Sed sit amet tortor at nisl malesuada tristique. Nulla faucibus …"

        from voteit.core.views.components.discussions import truncate
        
        self.assertEqual(truncate(text, 240), (truncated_text, True))
        
    def test_truncate_short(self):
        
        text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
               u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
               u"consectetur adipiscing elit. In hac habitasse platea dictumst."
                
        truncated_text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
                         u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
                         u"consectetur adipiscing elit. In hac habitasse platea dictumst."

        from voteit.core.views.components.discussions import truncate
        
        self.assertEqual(truncate(text, 240), (truncated_text, False))
        
    def test_truncate_exakt_length(self):
        
        text = u"Duis non tortor urna. Mauris at mi risus, non consectetur elit. " \
                "Donec consectetur tempor elementum. Nunc vehicula ipsum a dolor " \
                "mattis cursus. Maecenas eget eros mauris. Vestibulum ullamcorper " \
                "rutrum lectus a tempor. Vivamus consequat amet."
                
        truncated_text = u"Duis non tortor urna. Mauris at mi risus, non consectetur elit. " \
                          "Donec consectetur tempor elementum. Nunc vehicula ipsum a dolor " \
                          "mattis cursus. Maecenas eget eros mauris. Vestibulum ullamcorper " \
                          "rutrum lectus a tempor. Vivamus consequat amet."

        from voteit.core.views.components.discussions import truncate
        
        self.assertEqual(truncate(text, 240), (truncated_text, False))
        
    def test_truncate_no_length(self):
        
        text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
               u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
               u"consectetur adipiscing elit. In hac habitasse platea dictumst."
                
        truncated_text = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " \
                         u"Nam luctus porta justo a pulvinar. Lorem ipsum dolor sit amet, " \
                         u"consectetur adipiscing elit. In hac habitasse platea dictumst."

        from voteit.core.views.components.discussions import truncate
        
        self.assertEqual(truncate(text, None), (truncated_text, False))