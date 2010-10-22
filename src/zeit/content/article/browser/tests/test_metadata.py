# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

import zeit.content.article.testing


class HeadTest(zeit.content.article.testing.SeleniumTestCase):

    def setUp(self):
        super(HeadTest, self).setUp()
        self.open('/repository/online/2007/01/Somalia/@@checkout')
        self.selenium.waitForElementPresent('id=head.year')

    def test_form_should_save_entered_data(self):
        s = self.selenium
        s.assertValue('id=head.year', '2007')
        s.type('id=head.year', '2010')
        s.click('head.actions.apply')
        s.pause(250)
        # XXX there needs to be an indicator which shows that save is in
        # progress and when it's finished.
        s.clickAndWait('link=Edit contents')
        s.waitForElementPresent('id=head.year')
        s.assertValue('id=head.year', '2010')

    def test_change_in_ressort_should_update_subressort_list(self):
        s = self.selenium
        s.assertSelectedLabel('id=head.ressort', 'International')
        self.assertEqual(
            [u'(no value)', u'Meinung', u'Nahost', u'US-Wahl'],
            s.getSelectOptions('id=head.sub_ressort'))
        s.select('id=head.ressort', 'Deutschland')
        s.pause(100)
        self.assertEqual(
            [u'(no value)', u'Datenschutz', u'Integration',
             u'Joschka Fisher', u'Meinung'],
            s.getSelectOptions('id=head.sub_ressort'))

    def test_invalid_input_should_display_error_message(self):
        s = self.selenium
        s.assertValue('id=head.year', '2007')
        s.type('id=head.year', 'ASDF')
        s.click('head.actions.apply')
        s.waitForElementPresent('css=.inline-form div.error')
