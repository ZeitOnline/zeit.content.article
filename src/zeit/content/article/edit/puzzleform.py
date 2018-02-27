# -*- coding: utf-8 -*-
from zeit.cms.i18n import MessageFactory as _
import grokcore.component as grok
import zeit.content.article.edit.block
import zeit.content.article.edit.interfaces


class PuzzleForm(zeit.content.article.edit.block.Block):

    grok.implements(zeit.content.article.edit.interfaces.IPuzzleForm)
    type = 'puzzleform'

    puzzle_type = zeit.cms.content.property.ObjectPathProperty(
        '.puzzle_type',
        zeit.content.article.edit.interfaces.IPuzzleForm['puzzle_type'])

    year = zeit.cms.content.property.ObjectPathProperty(
        '.year', zeit.content.article.edit.interfaces.IPuzzleForm['year'])

    number = zeit.cms.content.property.ObjectPathProperty(
        '.number', zeit.content.article.edit.interfaces.IPuzzleForm['number'])


class Factory(zeit.content.article.edit.block.BlockFactory):

    produces = PuzzleForm
    title = _('Puzzle Form Block')
