# coding: utf-8
# Copyright (c) 2010-2012 gocept gmbh & co. kg
# See also LICENSE.txt

from zeit.content.article.article import Article
from zeit.workflow.interfaces import IReview
import mock
import unittest
import zeit.cms.testing
import zeit.content.article.testing


class Checkin(zeit.cms.testing.BrowserTestCase):

    layer = zeit.content.article.testing.ArticleLayer

    def test_validation_errors_should_be_displayed_at_checkin_button(self):
        with zeit.cms.testing.site(self.getRootFolder()):
            with zeit.cms.testing.interaction():
                self.repository['article'] = Article()
        b = self.browser
        b.open('http://localhost/++skin++vivi/repository/article/@@checkout')
        b.open('@@edit.form.checkin')
        self.assert_ellipsis('...Title:...Required input is missing...')
        self.assertTrue(b.getControl('Save').disabled)

    def test_checkin_does_not_set_last_semantic_change_by_default(self):
        b = self.browser
        b.open('http://localhost/++skin++vivi/repository/'
               'online/2007/01/Somalia/@@checkout')
        with mock.patch(
            'zeit.cms.checkout.browser.manager.Checkin.__call__') as checkin:
            checkin.return_value = None
            b.open('@@edit.form.checkin')
            b.getControl('Save').click()
            checkin.assert_called_with(semantic_change=False)

    def test_checkin_sets_last_semantic_change_if_checked(self):
        b = self.browser
        b.open('http://localhost/++skin++vivi/repository/'
               'online/2007/01/Somalia/@@checkout')
        with mock.patch(
            'zeit.cms.checkout.browser.manager.Checkin.__call__') as checkin:
            checkin.return_value = None
            b.open('@@edit.form.checkin')
            b.getControl(name='semantic_change').controls[0].selected = True
            b.getControl('Save').click()
            checkin.assert_called_with(semantic_change=True)


class WorkflowEndToEnd(
    zeit.content.article.edit.browser.testing.EditorTestCase):

    def test_checkin_redirects_to_repository(self):
        s = self.selenium
        self.open('/repository/online/2007/01/Somalia/@@checkout')
        s.waitForElementPresent('name=checkin')
        self.assertNotIn('repository', s.getLocation())
        s.clickAndWait('name=checkin')
        self.assertIn('repository', s.getLocation())

    def test_checkout_redirects_to_working_copy(self):
        s = self.selenium
        self.open('/repository/online/2007/01/Somalia/')
        checkout_button = 'xpath=//a[contains(@title, "Checkout")]'
        s.waitForElementPresent(checkout_button)
        self.assertIn('repository', s.getLocation())
        s.clickAndWait(checkout_button)
        self.assertNotIn('repository', s.getLocation())

    def test_publish_shows_lightbox(self):
        s = self.selenium
        self.open('/')  # XXX else the next open() fails as Unauthenticated
        self.open('/repository/online/2007/01/Somalia/')
        s.waitForElementPresent('id=publish')
        s.click('id=publish')
        s.waitForElementPresent('css=.lightbox')
        # lightbox content is covered by zeit.workflow, see there for detailed
        # tests

    def test_delete_shows_lightbox(self):
        s = self.selenium
        self.open('/') # XXX
        self.open('/repository/online/2007/01/Somalia/')
        s.waitForElementPresent('id=delete_from_repository')
        s.click('id=delete_from_repository')
        s.waitForElementPresent('css=.lightbox')


class Publish(zeit.cms.testing.BrowserTestCase):

    layer = zeit.content.article.testing.ArticleLayer

    def prepare_content(self, urgent):
        root = self.getRootFolder()
        with zeit.cms.testing.site(root):
            with zeit.cms.testing.interaction():
                content = zeit.cms.interfaces.ICMSContent(
                    'http://xml.zeit.de/online/2007/01/Somalia')
                IReview(content).urgent = urgent

    def test_smoke_publish_button_publishes_article(self):
        b = self.browser
        b.open('http://localhost/++skin++vivi/repository/'
               'online/2007/01/Somalia/@@checkout')
        b.open('@@edit.form.publish?show_form=1')
        b.getControl('Urgent').selected = True
        with mock.patch('zeit.cms.workflow.interfaces.IPublish') as publish:
            b.handleErrors = False
            b.getControl('Save & Publish').click()
            self.assertTrue(publish().publish.called)

    def test_urgent_denies_marking_edited_and_corrected(self):
        self.prepare_content(urgent=True)
        b = self.browser
        b.open('http://localhost/++skin++vivi/repository/'
               'online/2007/01/Somalia/@@checkout')
        b.open('@@edit.form.publish?show_form=1')
        self.assertTrue(b.getControl('Corrected').disabled)
        self.assertTrue(b.getControl('Edited').disabled)

    def test_non_urgent_allows_marking_edited_and_corrected(self):
        self.prepare_content(urgent=False)
        b = self.browser
        b.open('http://localhost/++skin++vivi/repository/'
               'online/2007/01/Somalia/@@checkout')
        b.open('@@edit.form.publish?show_form=1')
        self.assertFalse(b.getControl('Corrected').disabled)
        self.assertFalse(b.getControl('Edited').disabled)


class Delete(zeit.cms.testing.BrowserTestCase):

    layer = zeit.content.article.testing.ArticleLayer

    def test_checked_out_article_has_cancel_but_no_delete(self):
        b = self.browser
        b.open('http://localhost/++skin++vivi/repository/'
               'online/2007/01/Somalia/@@checkout')
        b.open('@@edit.form.checkin?show_form=1')
        self.assertNothingRaised(b.getLink, 'Cancel')
        self.assertNotIn('Delete', b.contents)

    def test_checked_in_article_has_delete_but_no_cancel(self):
        b = self.browser
        b.open('http://localhost/++skin++vivi/repository/'
               'online/2007/01/Somalia/@@edit.form.checkin?show_form=1')
        self.assertNothingRaised(b.getLink, 'Delete')
        self.assertNotIn('Cancel', b.contents)


@unittest.skip('FF shows an HTTP auth dialog for no reason')
class Objectlog(
    zeit.content.article.edit.browser.testing.EditorTestCase):

    def test_objectlog_is_wrapped(self):
        # this is a sanity check that the views are wired up correctly
        with zeit.cms.testing.site(self.getRootFolder()):
            with zeit.cms.testing.interaction():
                article = zeit.cms.interfaces.ICMSContent(
                    'http://xml.zeit.de/online/2007/01/Somalia')
                zeit.objectlog.interfaces.ILog(article).log('example message')
        self.open(
            'http://localhost/++skin++vivi/repository/online/2007/01/Somalia/')
        s = self.selenium
        s.waitForElementPresent('css=div.objectlog table.objectlog')
        s.assertText('css=div.objectlog table.objectlog', '*example message*')
