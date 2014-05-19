# Copyright (c) 2014 gocept gmbh & co. kg
# See also LICENSE.txt

import zeit.content.article.edit.browser.testing


class Form(zeit.content.article.edit.browser.testing.BrowserTestCase):

    block_type = 'liveblog'

    def test_inline_form_saves_values(self):
        self.get_article(with_empty_block=True)
        b = self.browser
        b.open(
            'editable-body/blockname/@@edit-%s?show_form=1' % self.block_type)
        b.getControl('Liveblog id').value = 'bloggy'
        b.getControl('Apply').click()
        b.open('@@edit-%s?show_form=1' % self.block_type)  # XXX
        self.assertEqual('bloggy', b.getControl('Liveblog id').value)