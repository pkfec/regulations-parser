# vim: set encoding=utf-8
from unittest import TestCase

from lxml import etree

from regparser.grammar import tokens
from regparser.notice import diff
from tests.xml_builder import XMLBuilderMixin


class NoticeDiffTests(XMLBuilderMixin, TestCase):
    def test_make_amendments(self):
        tokenized = [
            tokens.Paragraph(part='111'),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph(part='222'),
            tokens.Paragraph(part='333'),
            tokens.Paragraph(part='444'),
            tokens.Verb(tokens.Verb.DELETE, active=True),
            tokens.Paragraph(part='555'),
            tokens.Verb(tokens.Verb.MOVE, active=True),
            tokens.Paragraph(part='666'),
            tokens.Paragraph(part='777')
        ]
        amends = diff.make_amendments(tokenized)
        self.assertEqual(amends,
                         [diff.Amendment(tokens.Verb.PUT, '222'),
                          diff.Amendment(tokens.Verb.PUT, '333'),
                          diff.Amendment(tokens.Verb.PUT, '444'),
                          diff.Amendment(tokens.Verb.DELETE, '555'),
                          diff.Amendment(tokens.Verb.MOVE, '666', '777')])

    def test_compress_context_simple(self):
        tokenized = [
            tokens.Verb(tokens.Verb.PUT, active=True),
            #  part 9876, subpart A
            tokens.Context(['9876', 'Subpart:A']),
            #  section 12
            tokens.Context([None, None, '12']),
            #  12(f)(4)
            tokens.Paragraph(paragraphs=['f', '4']),
            #  12(f)
            tokens.Context([None, None, None, 'g']),
            #  12(g)(1)
            tokens.Paragraph(paragraphs=[None, '1']),
        ]
        converted, final_ctx = diff.compress_context(tokenized, [])
        self.assertEqual(converted, [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph(part='9876', subpart='A', section='12',
                             paragraphs=['f', '4']),
            tokens.Paragraph(part='9876', subpart='A', section='12',
                             paragraphs=['g', '1']),
        ])
        self.assertEqual(['9876', 'Subpart:A', '12', 'g', '1'], final_ctx)

    def test_compress_context_initial_context(self):
        tokenized = [tokens.Paragraph(paragraph='q')]
        converted, _ = diff.compress_context(tokenized, ['111', None, '12'])
        self.assertEqual(
            converted,
            [tokens.Paragraph(part='111', section='12', paragraph='q')])

    def test_compress_context_interpretations(self):
        tokenized = [
            tokens.Context(['123', 'Interpretations']),
            tokens.Paragraph(section='12', paragraphs=['a', '2', 'iii']),
            tokens.Paragraph(is_interp=True, paragraphs=[None, '3', 'v']),
            tokens.Context([None, 'Appendix:R']),
            tokens.Paragraph(is_interp=True, paragraphs=[None, '5'])
        ]
        converted, _ = diff.compress_context(tokenized, [])
        self.assertEqual(converted, [
            tokens.Paragraph(part='123', is_interp=True, section='12',
                             paragraphs=['(a)(2)(iii)', '3', 'v']),
            #   None because we are missing a layer
            tokens.Paragraph(part='123', is_interp=True, section='Appendix:R',
                             paragraphs=[None, '5'])
        ])

    def test_compress_context_in_tokenlists(self):
        tokenized = [
            tokens.Context(['123', 'Interpretations']),
            tokens.Paragraph(part='123', section='23', paragraph='a'),
            tokens.Verb(tokens.Verb.PUT, True),
            tokens.TokenList([
                tokens.Verb(tokens.Verb.POST, True),
                tokens.Paragraph(part='123', section='23',
                                 paragraphs=['a', '1']),
                tokens.Paragraph(paragraphs=[None, None, 'i']),
                tokens.Paragraph(section='23', paragraph='b')])]
        converted = diff.compress_context_in_tokenlists(tokenized)
        self.assertEqual(converted, [
            tokens.Context(['123', 'Interpretations']),
            tokens.Paragraph(part='123', section='23', paragraph='a'),
            tokens.Verb(tokens.Verb.PUT, True),
            tokens.TokenList([
                tokens.Verb(tokens.Verb.POST, True),
                tokens.Paragraph(part='123', section='23',
                                 paragraphs=['a', '1']),
                tokens.Paragraph(part='123', section='23',
                                 paragraphs=['a', '1', 'i']),
                tokens.Paragraph(part='123', section='23', paragraph='b')])])

    def test_resolve_confused_context(self):
        tokenized = [tokens.Context([None, None, '12', 'a', '2', 'iii'])]
        converted = diff.resolve_confused_context(
            tokenized, ['123', 'Interpretations'])
        self.assertEqual(
            converted, [tokens.Context([None, 'Interpretations', '12',
                                        '(a)(2)(iii)'])])

    def test_resolve_confused_context_appendix(self):
        tokenized = [tokens.Context([None, 'Appendix:A', '12'])]
        converted = diff.resolve_confused_context(
            tokenized, ['123', 'Interpretations'])
        self.assertEqual(
            converted, [tokens.Context([None, 'Interpretations', 'A',
                                        '(12)'])])

    def test_compress(self):
        self.assertEqual([1, 2, 3], diff.compress([1, 2, 3], []))
        self.assertEqual([1, 6, 3],
                         diff.compress([1, 2, 3, 4, 5], [None, 6, None]))
        self.assertEqual([2, 2, 5, 6], diff.compress([1, 2], [2, None, 5, 6]))

    def test_separate_tokenlist(self):
        tokenized = [
            tokens.Context(['1']),
            tokens.TokenList([
                tokens.Verb(tokens.Verb.MOVE, active=True),
                tokens.Context([None, '2'])
            ]),
            tokens.Paragraph(sub='3'),
            tokens.TokenList([tokens.Paragraph(section='b')])
        ]
        converted = diff.separate_tokenlist(tokenized)
        self.assertEqual(converted, [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.MOVE, active=True),
            tokens.Context([None, '2']),
            tokens.Paragraph(sub='3'),
            tokens.Paragraph(section='b')
        ])

    def test_context_to_paragraph(self):
        tokenized = [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['2']),
            tokens.Context(['3'], certain=True),
            tokens.Context(['4'])
        ]
        converted = diff.context_to_paragraph(tokenized)
        self.assertEqual(converted, [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Paragraph(part='2'),
            tokens.Context(['3'], certain=True),
            tokens.Paragraph(part='4')
        ])

    def test_context_to_paragraph_exceptions(self):
        tokenized = [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['2']),
            tokens.Paragraph(part='3')
        ]
        converted = diff.context_to_paragraph(tokenized)
        self.assertEqual(tokenized, converted)

        tokenized = [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['2']),
            tokens.TokenList([tokens.Paragraph(part='3')])
        ]
        converted = diff.context_to_paragraph(tokenized)
        self.assertEqual(tokenized, converted)

    def test_switch_passive(self):
        tokenized = [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['2'])
        ]
        converted = diff.switch_passive(tokenized)
        self.assertEqual(tokenized, converted)

        tokenized = [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.PUT, active=False),
            tokens.Context(['2']),
            tokens.Context(['3']),
            tokens.Verb(tokens.Verb.MOVE, active=False),
        ]
        converted = diff.switch_passive(tokenized)
        self.assertEqual(converted, [
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.MOVE, active=True),
            tokens.Context(['2']),
            tokens.Context(['3']),
        ])

        tokenized = [
            tokens.Context(['1']),
            tokens.Verb(tokens.Verb.MOVE, active=False),
            tokens.Context(['2']),
            tokens.Context(['3']),
            tokens.Verb(tokens.Verb.PUT, active=False)]
        converted = diff.switch_passive(tokenized)
        self.assertEqual(converted, [
            tokens.Verb(tokens.Verb.MOVE, active=True),
            tokens.Context(['1']),
            tokens.Context(['2']),
            tokens.Verb(tokens.Verb.PUT, active=True),
            tokens.Context(['3']),
        ])

    def test_find_section(self):
        with self.tree.builder('REGTEXT') as regtext:
            regtext.AMDPAR("In 200.1 revise paragraph (b) as follows:")
            with regtext.SECTION() as section:
                section.SECTNO("200.1")
                section.SUBJECT("Authority and Purpose.")
                section.P(" (b) This part is very important. ")
            regtext.AMDPAR("In 200.3 revise paragraph (b)(1) as follows:")
            with regtext.SECTION() as section:
                section.SECTNO("200.3")
                section.SUBJECT("Definitions")
                section.P(" (b)(1) Define a term here. ")

        notice_xml = self.tree.render_xml()
        amdpar_xml = notice_xml.xpath('//AMDPAR')[0]
        section = diff.find_section(amdpar_xml)
        self.assertEqual(section.tag, 'SECTION')

        sectno_xml = section.xpath('./SECTNO')[0]
        self.assertEqual(sectno_xml.text, '200.1')

    def test_find_subpart(self):
        with self.tree.builder('REGTEXT', PART='105', TITLE='12') as regtext:
            regtext.AMDPAR("6. Add subpart B to read as follows:")
            with regtext.SUBPART() as subpart:
                subpart.HD(u"Subpart B—Requirements", SOURCE="HED")
                with subpart.SECTION() as section:
                    section.SECTNO("105.30")
                    section.SUBJECT("First In New Subpart")
                    section.P("For purposes of this subpart, the follow "
                              "apply:")
                    section.P('(a) "Agent" means agent.')

        notice_xml = self.tree.render_xml()
        amdpar_xml = notice_xml.xpath('//AMDPAR')[0]
        subpart = diff.find_subpart(amdpar_xml)
        self.assertTrue(subpart is not None)

        headings = [s for s in subpart if s.tag == 'HD']
        self.assertEqual(headings[0].text, u"Subpart B—Requirements")

    def test_is_designate_token(self):
        class Noun(tokens.Token):
            def __init__(self, noun):
                self.noun = noun

        token = tokens.Verb(tokens.Verb.DESIGNATE, True)
        self.assertTrue(diff.is_designate_token(token))

        token = tokens.Verb(tokens.Verb.MOVE, True)
        self.assertFalse(diff.is_designate_token(token))

        token = Noun('TABLE')
        self.assertFalse(diff.is_designate_token(token))

    def list_of_tokens(self):
        designate_token = tokens.Verb(tokens.Verb.DESIGNATE, True)
        move_token = tokens.Verb(tokens.Verb.MOVE, True)
        return [designate_token, move_token]

    def test_contains_one_designate_token(self):
        tokenized = self.list_of_tokens()
        self.assertTrue(diff.contains_one_designate_token(tokenized))

        designate_token_2 = tokens.Verb(tokens.Verb.DESIGNATE, True)
        tokenized.append(designate_token_2)
        self.assertFalse(diff.contains_one_designate_token(tokenized))

    def test_contains_one_tokenlist(self):
        token_list = self.list_of_tokens()

        designate_token_2 = tokens.Verb(tokens.Verb.DESIGNATE, True)
        tokenized = [tokens.TokenList(token_list), designate_token_2]
        self.assertTrue(diff.contains_one_tokenlist(tokenized))

        tokenized = [tokens.TokenList(token_list),
                     designate_token_2, tokens.TokenList(token_list)]
        self.assertFalse(diff.contains_one_tokenlist(tokenized))

    def test_contains_one_context(self):
        tokenized = self.list_of_tokens()
        context = tokens.Context(['200', '1'])
        tokenized.append(context)

        self.assertTrue(diff.contains_one_context(tokenized))

        designate_token = tokens.Verb(tokens.Verb.DESIGNATE, True)
        tokenized.append(designate_token)
        tokenized.append(tokens.Context(['200', '2']))

        self.assertFalse(diff.contains_one_context(tokenized))

    def paragraph_token_list(self):
        paragraph_tokens = [
            tokens.Paragraph(part='200', sub='1', section='a'),
            tokens.Paragraph(part='200', sub='1', section='b')]
        return tokens.TokenList(paragraph_tokens)

    def test_deal_with_subpart_adds(self):
        designate_token = tokens.Verb(tokens.Verb.DESIGNATE, True)
        token_list = self.paragraph_token_list()
        context = tokens.Context(['Subpart', 'A'])

        tokenized = [designate_token, token_list, context]

        toks, subpart_added = diff.deal_with_subpart_adds(tokenized)
        self.assertTrue(subpart_added)

        paragraph_found = False
        for t in toks:
            self.assertFalse(isinstance(t, tokens.Context))

            if isinstance(t, tokens.Paragraph):
                self.assertEqual(t.label, ['Subpart', 'A'])
                paragraph_found = True

        self.assertTrue(diff.contains_one_tokenlist(toks))
        self.assertTrue(diff.contains_one_designate_token(toks))
        self.assertTrue(paragraph_found)

    def test_deal_with_subpart_adds_no_subpart(self):
        designate_token = tokens.Verb(tokens.Verb.DESIGNATE, True)
        token_list = self.paragraph_token_list()
        tokenized = [designate_token, token_list]

        toks, subpart_added = diff.deal_with_subpart_adds(tokenized)
        self.assertFalse(subpart_added)

    def test_get_destination_normal(self):
        subpart_token = tokens.Paragraph(part='205', subpart='A')
        tokenized = [subpart_token]

        self.assertEqual(diff.get_destination(tokenized, '205'),
                         '205-Subpart:A')

    def test_get_destination_no_reg_part(self):
        subpart_token = tokens.Paragraph(subpart='J')
        tokenized = [subpart_token]

        self.assertEqual(diff.get_destination(tokenized, '205'),
                         '205-Subpart:J')

    def test_handle_subpart_designate(self):
        token_list = self.paragraph_token_list()
        subpart_token = tokens.Paragraph(subpart='J')
        tokenized = [token_list, subpart_token]

        amendment = diff.handle_subpart_amendment(tokenized)

        self.assertEqual(amendment.action, tokens.Verb.DESIGNATE)
        labels = [['200', '1', 'a'], ['200', '1', 'b']]
        self.assertEqual(amendment.labels, labels)
        self.assertEqual(amendment.destination, ['200', 'Subpart', 'J'])

    def test_make_amendments_subpart(self):
        token_list = self.paragraph_token_list()
        subpart_token = tokens.Paragraph(subpart='J')
        tokenized = [token_list, subpart_token]
        amends = diff.make_amendments(tokenized, subpart=True)

        amendment = amends[0]
        self.assertEqual(amendment.action, tokens.Verb.DESIGNATE)
        labels = [['200', '1', 'a'], ['200', '1', 'b']]
        self.assertEqual(amendment.labels, labels)
        self.assertEqual(amendment.destination, ['200', 'Subpart', 'J'])

    def test_new_subpart_added(self):
        amended_label = diff.Amendment('POST', '200-Subpart:B')
        self.assertTrue(diff.new_subpart_added(amended_label))

        amended_label = diff.Amendment('PUT', '200-Subpart:B')
        self.assertFalse(diff.new_subpart_added(amended_label))

        amended_label = diff.Amendment('POST', '200-Subpart:B-a-3')
        self.assertFalse(diff.new_subpart_added(amended_label))

    def test_switch_part_context(self):
        initial_context = ['105', '2']

        tokenized = [
            tokens.Paragraph(part='203', sub='2', section='x'),
            tokens.Verb(tokens.Verb.DESIGNATE, True)]

        self.assertEqual(diff.switch_part_context(tokenized, initial_context),
                         [])

        tokenized = [
            tokens.Paragraph(part='105', sub='4', section='j', paragraph='iv'),
            tokens.Verb(tokens.Verb.DESIGNATE, True)]

        self.assertEqual(diff.switch_part_context(tokenized, initial_context),
                         initial_context)

        tokenized = [
            tokens.Context(['', '4', 'j', 'iv']),
            tokens.Verb(tokens.Verb.DESIGNATE, True)]

        self.assertEqual(diff.switch_part_context(tokenized, initial_context),
                         initial_context)

    def test_switch_level2_context(self):
        """The presence of certain types of context should apply throughout
        the amendment"""
        initial = ['105', None, '2']
        tokenized = [tokens.Paragraph(), tokens.Verb('verb', True)]
        transform = diff.switch_level2_context  # shorthand

        self.assertEqual(transform(tokenized, initial), initial)

        context = tokens.Context(['105', 'Subpart:G'], certain=False)
        tokenized.append(context)
        self.assertEqual(transform(tokenized, initial), initial)

        context.certain = True
        self.assertEqual(transform(tokenized, initial),
                         ['105', 'Subpart:G', '2'])

        # Don't try to proceed if multiple contexts are present
        tokenized.append(tokens.Context(['105', 'Appendix:Q'], certain=True))
        self.assertEqual(transform(tokenized, initial), initial)

    def test_fix_section_node(self):
        with self.tree.builder("REGTEXT") as regtext:
            regtext.P("paragraph 1")
            regtext.P("paragraph 2")
        paragraphs = [p for p in self.tree.render_xml() if p.tag == 'P']

        with self.tree.builder("REGTEXT") as regtext:
            with regtext.SECTION() as section:
                section.SECTNO(" 205.4 ")
                section.SUBJECT("[Corrected]")
            regtext.AMDPAR(u"3. In § 105.1, revise paragraph (b) to read as "
                           "follows:")
        par = self.tree.render_xml().xpath('//AMDPAR')[0]
        section = diff.fix_section_node(paragraphs, par)
        self.assertNotEqual(None, section)
        section_paragraphs = [p for p in section if p.tag == 'P']
        self.assertEqual(2, len(section_paragraphs))

        self.assertEqual(section_paragraphs[0].text, 'paragraph 1')
        self.assertEqual(section_paragraphs[1].text, 'paragraph 2')

    def test_find_section_paragraphs(self):
        with self.tree.builder('REGTEXT') as regtext:
            with regtext.SECTION() as section:
                section.SECTNO(" 205.4 ")
                section.SUBJECT("[Corrected]")
            regtext.AMDPAR(u"3. In § 105.1, revise paragraph (b) to read as "
                           "follows:")
            regtext.P("(b) paragraph 1")

        amdpar = self.tree.render_xml().xpath('//AMDPAR')[0]
        section = diff.find_section(amdpar)
        self.assertNotEqual(None, section)
        paragraphs = [p for p in section if p.tag == 'P']
        self.assertEqual(paragraphs[0].text, '(b) paragraph 1')

    def test_find_lost_section(self):
        with self.tree.builder("PART") as part:
            with part.REGTEXT() as regtext:
                regtext.AMDPAR(u"3. In § 105.1, revise paragraph (b) to read "
                               "as follows:")
            with part.REGTEXT() as regtext:
                with regtext.SECTION() as section:
                    section.SECTNO(" 205.4 ")
                    section.SUBJECT("[Corrected]")
        amdpar = self.tree.render_xml().xpath('//AMDPAR')[0]
        section = diff.find_lost_section(amdpar)
        self.assertNotEqual(None, section)

    def test_find_section_lost(self):
        with self.tree.builder("PART") as part:
            with part.REGTEXT() as regtext:
                regtext.AMDPAR(u"3. In § 105.1, revise paragraph (b) to read "
                               "as follows:")
            with part.REGTEXT() as regtext:
                with regtext.SECTION() as section:
                    section.SECTNO(" 205.4 ")
                    section.SUBJECT("[Corrected]")
        amdpar = self.tree.render_xml().xpath('//AMDPAR')[0]
        section = diff.find_section(amdpar)
        self.assertNotEqual(None, section)

    def test_remove_false_deletes(self):
        tokenized = [
            tokens.Paragraph(part='444'),
            tokens.Verb(tokens.Verb.DELETE, active=True)]

        text = "Remove the semi-colong at the end of paragraph 444"
        new_tokenized = diff.remove_false_deletes(tokenized, text)
        self.assertEqual([], new_tokenized)

    def test_multiple_moves(self):
        tokenized = [
            tokens.TokenList([tokens.Paragraph(part='444', sub='1'),
                              tokens.Paragraph(part='444', sub='2')]),
            tokens.Verb(tokens.Verb.MOVE, active=False),
            tokens.TokenList([tokens.Paragraph(part='444', sub='3'),
                              tokens.Paragraph(part='444', sub='4')])]
        tokenized = diff.multiple_moves(tokenized)
        self.assertEqual(
            tokenized, [tokens.Verb(tokens.Verb.MOVE, active=True),
                        tokens.Paragraph(part='444', sub='1'),
                        tokens.Paragraph(part='444', sub='3'),
                        tokens.Verb(tokens.Verb.MOVE, active=True),
                        tokens.Paragraph(part='444', sub='2'),
                        tokens.Paragraph(part='444', sub='4')])

        # Not even number of elements on either side
        tokenized = [
            tokens.TokenList([tokens.Paragraph(part='444', sub='1'),
                              tokens.Paragraph(part='444', sub='2')]),
            tokens.Verb(tokens.Verb.MOVE, active=False),
            tokens.TokenList([tokens.Paragraph(part='444', sub='3')])]
        self.assertEqual(tokenized, diff.multiple_moves(tokenized))

        # Paragraphs on either side of a move
        tokenized = [tokens.Paragraph(part='444', sub='1'),
                     tokens.Verb(tokens.Verb.MOVE, active=False),
                     tokens.Paragraph(part='444', sub='3')]
        self.assertEqual(tokenized, diff.multiple_moves(tokenized))

    def test_parse_amdpar_newly_redesignated(self):
        text = "Paragraphs 3.ii, 3.iii, 4 and newly redesignated paragraph "
        text += "10 are revised."
        xml = etree.fromstring('<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml,
                                      ['1111', 'Interpretations', '2', '(a)'])
        self.assertEqual(4, len(amends))
        self.assertEqual(['1111', '2', 'a', 'Interp', '3', 'ii'],
                         amends[0].label)
        self.assertEqual(['1111', '2', 'a', 'Interp', '3', 'iii'],
                         amends[1].label)
        self.assertEqual(['1111', '2', 'a', 'Interp', '4'],
                         amends[2].label)
        self.assertEqual(['1111', '2', 'a', 'Interp', '10'],
                         amends[3].label)
        for amend in amends:
            self.assertEqual(amend.action, 'PUT')

    def test_parse_amdpar_interp_phrase(self):
        text = u"In Supplement I to part 999, under"
        text += u'<E T="03">Section 999.3—Header,</E>'
        text += u"under"
        text += u'<E T="03">3(b) Subheader,</E>'
        text += u"new paragraph 1.iv is added:"
        xml = etree.fromstring(u'<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111'])
        self.assertEqual(1, len(amends))
        self.assertEqual('POST', amends[0].action)
        self.assertEqual(['999', '3', 'b', 'Interp', '1', 'iv'],
                         amends[0].label)

    def test_parse_amdpar_interp_heading(self):
        text = "ii. The heading for 35(b) blah blah is revised."
        xml = etree.fromstring(u'<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', 'Interpretations'])
        self.assertEqual(1, len(amends))
        self.assertEqual('PUT', amends[0].action)
        self.assertEqual('[title]', amends[0].field)
        self.assertEqual(['1111', '35', 'b', 'Interp'], amends[0].label)

    def test_parse_amdpar_interp_context(self):
        text = "b. 35(b)(1) Some title and paragraphs 1, 2, and 3 are added."
        xml = etree.fromstring(u'<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', 'Interpretations'])
        self.assertEqual(4, len(amends))
        for amd in amends:
            self.assertEqual('POST', amd.action)
        amd35b1, amd35b1_1, amd35b1_2, amd35b1_3 = amends
        self.assertEqual(['1111', '35', 'b', '1', 'Interp'], amd35b1.label)
        self.assertEqual(['1111', '35', 'b', '1', 'Interp', '1'],
                         amd35b1_1.label)
        self.assertEqual(['1111', '35', 'b', '1', 'Interp', '2'],
                         amd35b1_2.label)
        self.assertEqual(['1111', '35', 'b', '1', 'Interp', '3'],
                         amd35b1_3.label)

    def test_parse_amdpar_interp_redesignated(self):
        text = "Paragraph 1 under 51(b) is redesignated as paragraph 2 "
        text += "under subheading 51(b)(1) and revised"
        xml = etree.fromstring(u'<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', 'Interpretations'])
        self.assertEqual(2, len(amends))
        delete, add = amends
        self.assertEqual('DELETE', delete.action)
        self.assertEqual(['1111', '51', 'b', 'Interp', '1'], delete.label)
        self.assertEqual('POST', add.action)
        self.assertEqual(['1111', '51', 'b', '1', 'Interp', '2'], add.label)

    def test_parse_amdpar_interp_entries(self):
        text = "Entries for 12(c)(3)(ix)(A) and (B) are added."
        xml = etree.fromstring('<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', 'Interpretations'])
        self.assertEqual(2, len(amends))
        a, b = amends
        self.assertEqual('POST', a.action)
        self.assertEqual(['1111', '12', 'c', '3', 'ix', 'A', 'Interp'],
                         a.label)
        self.assertEqual('POST', b.action)
        self.assertEqual(['1111', '12', 'c', '3', 'ix', 'B', 'Interp'],
                         b.label)

    def test_parse_amdpar_and_and(self):
        text = "12(a) 'Titles and Paragraphs' and paragraph 3 are added"
        xml = etree.fromstring('<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', 'Interpretations'])
        self.assertEqual(2, len(amends))
        a, b = amends
        self.assertEqual('POST', a.action)
        self.assertEqual(['1111', '12', 'a', 'Interp'],
                         a.label)
        self.assertEqual('POST', b.action)
        self.assertEqual(['1111', '12', 'a', 'Interp', '3'],
                         b.label)

    def test_parse_amdpar_and_in_tags(self):
        text = "Under <E>Appendix A - Some phrase and another</E>, paragraph "
        text += "3 is added"
        xml = etree.fromstring('<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', 'Interpretations'])
        self.assertEqual(1, len(amends))
        amend = amends[0]
        self.assertEqual('POST', amend.action)
        self.assertEqual(['1111', 'A', 'Interp', '3'], amend.label)

    def test_parse_amdpar_verbs_ands(self):
        text = "Under 45(a)(1) Title, paragraphs 1 and 2 are removed, and "
        text += "45(a)(1)(i) Deeper Title and paragraphs 1 and 2 are added"
        xml = etree.fromstring('<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', 'Interpretations'])
        self.assertEqual(5, len(amends))
        a11, a12, a1i, a1i1, a1i2 = amends
        self.assertEqual('DELETE', a11.action)
        self.assertEqual(['1111', '45', 'a', '1', 'Interp', '1'], a11.label)
        self.assertEqual('DELETE', a12.action)
        self.assertEqual(['1111', '45', 'a', '1', 'Interp', '2'], a12.label)

        self.assertEqual('POST', a1i.action)
        self.assertEqual(['1111', '45', 'a', '1', 'i', 'Interp'], a1i.label)
        self.assertEqual('POST', a1i1.action)
        self.assertEqual(['1111', '45', 'a', '1', 'i', 'Interp', '1'],
                         a1i1.label)
        self.assertEqual('POST', a1i2.action)
        self.assertEqual(['1111', '45', 'a', '1', 'i', 'Interp', '2'],
                         a1i2.label)

    def test_parse_amdpar_add_field(self):
        text = "Adding introductory text to paragraph (c)"
        xml = etree.fromstring('<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', None, '12'])
        self.assertEqual(1, len(amends))
        amd = amends[0]
        self.assertEqual(amd.action, tokens.Verb.PUT)
        self.assertEqual(amd.label, ['1111', '12', 'c'])
        self.assertEqual(amd.field, '[text]')

    def test_parse_amdpar_moved_then_modified(self):
        text = "Under Paragraph 22(a), paragraph 1 is revised, paragraph "
        text += "2 is redesignated as paragraph 3 and revised, and new "
        text += "paragraph 2 is added."
        xml = etree.fromstring('<AMDPAR>%s</AMDPAR>' % text)
        amends, _ = diff.parse_amdpar(xml, ['1111', 'Interpretations'])
        self.assertEqual(4, len(amends))
        a1, a2del, a3, a2add = amends
        self.assertEqual(a1.action, tokens.Verb.PUT)
        self.assertEqual(a1.label, ['1111', '22', 'a', 'Interp', '1'])
        self.assertEqual(a2del.action, tokens.Verb.DELETE)
        self.assertEqual(a2del.label, ['1111', '22', 'a', 'Interp', '2'])
        self.assertEqual(a3.action, tokens.Verb.POST)
        self.assertEqual(a3.label, ['1111', '22', 'a', 'Interp', '3'])
        self.assertEqual(a2add.action, tokens.Verb.POST)
        self.assertEqual(a2add.label, ['1111', '22', 'a', 'Interp', '2'])

    def test_parse_amdpar_subject_group(self):
        xml = etree.fromstring(
            '<AMDPAR>8. Section 479.90a is added to '
            '[subject-group(Exemptions Relating to Transfers of Firearms)] '
            'to read as follows.</AMDPAR>')
        amends, _ = diff.parse_amdpar(xml, [])
        self.assertEqual(1, len(amends))
        self.assertEqual(amends[0].action, tokens.Verb.POST)
        self.assertEqual(amends[0].label, ['479', '90a'])
        self.assertEqual(amends[0].original_label, '479-Subjgrp:ERtToF-90a')


class AmendmentTests(TestCase):
    def test_fix_label(self):
        """Fix label converts between the AMDPAR label format and the Node
        label format"""
        tests = {
            '1005-Interpretations': ['1005', 'Interp'],
            '1005-Interpretations-31-(b)(1)-3':
                ['1005', '31', 'b', '1', 'Interp', '3'],
            '1005-Interpretations-31-(b)(1)-3[title]':
                ['1005', '31', 'b', '1', 'Interp', '3'],
            '1005-Interpretations-31-(c)-2-xi':
                ['1005', '31', 'c', 'Interp', '2', 'xi'],
            '1005-Interpretations-31-()-2-xi':
                ['1005', '31', 'Interp', '2', 'xi'],
            '1005-Interpretations-Appendix:A-2':
                ['1005', 'A', '2', 'Interp'],
            '1005-Appendix:A-2': ['1005', 'A', '2'],
            '1005-Subpart:A-2': ['1005', '2'],
            '1005-Subjgrp:AbCd-2': ['1005', '2']
        }

        for in_label, out_label in tests.items():
            amd = diff.Amendment('action', in_label)
            self.assertEqual(amd.label, out_label)

    def test_amendment_heading(self):
        amendment = diff.Amendment('PUT', '100-2-a[heading]')
        self.assertEqual(amendment.action, 'PUT')
        self.assertEqual(amendment.label, ['100', '2', 'a'])
        self.assertEqual(amendment.field, '[heading]')

    def test_tree_format_level2(self):
        for label, expected in (
                ('100', None),
                ('100-Interpretations', None),
                ('100-Subpart:A-105', ['100', 'Subpart', 'A']),
                ('100-Subjgrp:AbCdE', ['100', 'Subjgrp', 'AbCdE']),
                ('100-Appendix:R', ['100', 'R'])):
            self.assertEqual(
                diff.Amendment('VERB', label).tree_format_level2(),
                expected)


class DesignateAmendmentTests(TestCase):
    def test_fix_interp_format(self):
        amd = diff.DesignateAmendment(
            'action', [], '1005-Interpretations-31-(b)(1)-3')
        self.assertEqual(amd.destination,
                         ['1005', '31', 'b', '1', 'Interp', '3'])
