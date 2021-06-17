__doc__ = """
A class to hold a single substitution (i.e. a single line inside a lookup).
"""

import re
import copy


class SequenceElement:
    """
    Holds a element of input for a substitution.
    Can either be a single glyph, an inline class or a referenced class name.
    The element can be a target.
    """

    def __init__(self, element):
        self.name = element
        self.is_target = element[-1] == "'"
        self.is_context = None
        self.value = element if not self.is_target else element[:-1]
        self.glyph_names = []

        if element[0] == '@':
            self.type = 'class'
        elif element[0] == '[' and ']' in element:
            self.type = 'inline_class'
            try:
                self.glyph_names = re.search(r'\[(.+)\]', element).group(1).split(' ')
            except AttributeError:
                pass

        elif element.startswith('lookup '):
            self.type = 'lookup_ref'
            self.lookup_ref = element[len('lookup '):]
        else:
            self.type = 'glyph'
            self.glyph_names = [self.value]

        self.glyph_names = [gn for gn in self.glyph_names if not gn.startswith('@') and gn]

    def __repr__(self):
        return '<OpentypeObject SequenceElement \'{0}\' type={1} is_target={2}>'.format(self.value, self.type, self.is_target)


class Substitution:
    def __init__(self, code=None, script=None, language=None):
        self.raw_code = code

        self.input_sequence = []
        self.output_sequence = []

        self.input_glyphs = []
        self.output_glyphs = []

        self.all_glyphs = []

        self.script = script
        self.language = language
        self.is_chaining = False
        self.is_contextual = False

        if code:
            self.parse_code()

    def __repr__(self):
        return '<OpentypeObject Substitution with {0} input and {1} output elements>'.format(len(self.input_sequence), len(self.output_sequence))

    def parse_code(self):
        input_sequence_search = re.search(r'sub (.+?) by', self.raw_code)
        output_sequence_search = re.search(r' by (.+?);', self.raw_code)
        if not input_sequence_search or not output_sequence_search:
            if re.search('sub .+? lookup .+', self.raw_code):
                self.is_chaining = True
                input_sequence_search = re.search(r'sub (.+);', self.raw_code)
            else:
                return

        try:
            input_sequence = input_sequence_search.group(1)
            self.input_sequence = self.parse_sequence(input_sequence)
        except AttributeError:
            pass

        try:
            output_sequence = output_sequence_search.group(1)
            self.output_sequence = self.parse_sequence(output_sequence)
        except AttributeError:
            pass

        for ie in self.input_sequence:
            self.input_glyphs += ie.glyph_names
        for ie in self.output_sequence:
            self.output_glyphs += ie.glyph_names
        self.all_glyphs = self.input_glyphs + self.output_glyphs

    def parse_sequence(self, text_sequence):
        """
        Takes a string of glyphs or classes and returns a list of sequenceElement objects.
        """

        # prep inline_classes
        inline_classes = {}
        for i, inline_class in enumerate(re.findall(r"(\[.+?\]'?)", text_sequence)):
            inline_class_placeholder = 'inline_class_{}'.format(i)
            text_sequence = text_sequence.replace(inline_class, '{' + inline_class_placeholder + '}')
            inline_classes[inline_class_placeholder] = inline_class

        lookup_refs = {}
        for i, lookup_ref in enumerate(re.findall(r"(lookup [^\s]+)", text_sequence)):
            lookup_ref_placeholder = 'lookup_ref_{}'.format(i)
            text_sequence = text_sequence.replace(lookup_ref, '{' + lookup_ref_placeholder + '}')
            lookup_refs[lookup_ref_placeholder] = lookup_ref

        object_sequence = []
        seen_target = False
        for element in text_sequence.split(' '):
            # element = element.format(**inline_classes)
            element = inline_classes.get(element[1:-1], element)
            element = lookup_refs.get(element[1:-1], element)
            input_element = SequenceElement(element)
            if input_element.is_target:
                seen_target = True
            object_sequence.append(input_element)

        if seen_target:
            self.is_contextual = True
            for obj in object_sequence:
                obj.is_context = not obj.is_target

        return object_sequence

    def write(self, tab_level=0):
        string = None
        if self.is_chaining:
            string = '{tab}sub {in_seq};'.format(
                in_seq=self.sequence_to_str(self.input_sequence),
                tab='\t' * tab_level,
            )
        else:
            string = '{tab}sub {in_seq} by {out_seq};'.format(
                in_seq=self.sequence_to_str(self.input_sequence),
                out_seq=self.sequence_to_str(self.output_sequence),
                tab='\t' * tab_level,
            )

        return string

    @staticmethod
    def sequence_to_str(object_list):
        strs = [o.value if not o.is_target else o.value + "'" for o in object_list]
        return ' '.join(strs)

    def subset(self, scripts=None, languages=None, glyphs=None):
        new = copy.copy(self)
        if all([x is None for x in [scripts, languages, glyphs]]):
            return new

        if scripts and self.script not in scripts:
            return

        if languages and self.language not in languages:
            return

        if glyphs:
            if not isinstance(glyphs, list):
                glyphs = glyphs.split(' ')

            # If this substitution's glyphs are not a complete subset of the supplied glyphs
            if not set(self.all_glyphs) <= set(glyphs):
                return

        return new


if __name__ == "__main__":

    f = Substitution("	sub [@DevaIMatraRephs @DevaIMatraRephAnusvaras @DevaIMatraAnusvaras] @DevaFullforms' lookup removeReph [anusvara-deva reph-deva reph_anusvara-deva]';")
    print(f.raw_code)
    print(f.write())
    a = f.subset(scripts=['latn', None], glyphs='A Aacute Abreve Abreveacute Abrevedotbelow Abrevegrave Abrevehookabove Abrevetilde Acircumflex Acircumflexacute Acircumflexdotbelow Acircumflexgrave Acircumflexhookabove Acircumflextilde Adblgrave Adieresis Adotbelow Agrave Ahookabove Ainvertedbreve Amacron Aogonek Aring Aringacute Atilde AE AEacute B C Cacute Ccaron Ccedilla Ccircumflex Cdotaccent D DZcaron Eth Dcaron Dcroat Dzcaron E Eacute Ebreve Ecaron Ecircumflex Ecircumflexacute Ecircumflexdotbelow Ecircumflexgrave Ecircumflexhookabove Ecircumflextilde Edblgrave Edieresis Edotaccent Edotbelow Egrave Ehookabove Einvertedbreve Emacron Eogonek Etilde F G Gbreve Gcaron Gcircumflex Gcommaaccent Gdotaccent H Hbar Hcircumflex I IJ Iacute Ibreve Icircumflex Idblgrave Idieresis Idotaccent Idotbelow Igrave Ihookabove Iinvertedbreve Imacron Iogonek Itilde J Jcircumflex K Kcommaaccent L LJ Lacute Lcaron Lcommaaccent Ldot Lj Lslash M N NJ Nacute Ncaron Ncommaaccent Eng Nj Ntilde O Oacute Obreve Ocircumflex Ocircumflexacute Ocircumflexdotbelow Ocircumflexgrave Ocircumflexhookabove Ocircumflextilde Odblgrave Odieresis Odieresismacron Odotaccentmacron Odotbelow Ograve Ohookabove Ohorn Ohornacute Ohorndotbelow Ohorngrave Ohornhookabove Ohorntilde Ohungarumlaut Oinvertedbreve Omacron Oogonek Oslash Oslashacute Otilde Otildemacron OE P Thorn Q R Racute Rcaron Rcommaaccent Rdblgrave Rinvertedbreve S Sacute Scaron Scedilla Scircumflex Scommaaccent Germandbls Schwa T Tbar Tcaron Tcedilla Tcommaaccent U Uacute Ubreve Ucircumflex Udblgrave Udieresis Udotbelow Ugrave Uhookabove Uhorn Uhornacute Uhorndotbelow Uhorngrave Uhornhookabove Uhorntilde Uhungarumlaut Uinvertedbreve Umacron Uogonek Uring Utilde V W Wacute Wcircumflex Wdieresis Wgrave X Y Yacute Ycircumflex Ydieresis Ydotbelow Ygrave Yhookabove Ymacron Ytilde Z Zacute Zcaron Zdotaccent a aacute abreve abreveacute abrevedotbelow abrevegrave abrevehookabove abrevetilde acircumflex acircumflexacute acircumflexdotbelow acircumflexgrave acircumflexhookabove acircumflextilde adblgrave adieresis adotbelow agrave ahookabove ainvertedbreve amacron aogonek aring aringacute atilde ae aeacute b c cacute ccaron ccedilla ccircumflex cdotaccent d eth eth.ss01 dcaron dcroat dzcaron e eacute ebreve ecaron ecircumflex ecircumflexacute ecircumflexdotbelow ecircumflexgrave ecircumflexhookabove ecircumflextilde edblgrave edieresis edotaccent edotbelow egrave ehookabove einvertedbreve emacron eogonek etilde schwa f g gbreve gcaron gcircumflex gcommaaccent gdotaccent h hbar hcircumflex i idotless iacute ibreve icircumflex idblgrave idieresis idotaccent idotbelow igrave ihookabove iinvertedbreve ij imacron iogonek itilde j jdotless jcircumflex k kcommaaccent kgreenlandic l lacute lcaron lcommaaccent ldot lj lslash m n nacute napostrophe ncaron ncommaaccent eng nj ntilde o oacute obreve ocircumflex ocircumflexacute ocircumflexdotbelow ocircumflexgrave ocircumflexhookabove ocircumflextilde odblgrave odieresis odieresismacron odotaccentmacron odotbelow ograve ohookabove ohorn ohornacute ohorndotbelow ohorngrave ohornhookabove ohorntilde ohungarumlaut oinvertedbreve omacron oogonek oslash oslashacute otilde otildemacron oe p thorn q r racute rcaron rcommaaccent rdblgrave rinvertedbreve s sacute scaron scedilla scircumflex scommaaccent germandbls t tbar tcaron tcedilla tcommaaccent u uacute ubreve ucircumflex udblgrave udieresis udotbelow ugrave uhookabove uhorn uhornacute uhorndotbelow uhorngrave uhornhookabove uhorntilde uhungarumlaut uinvertedbreve umacron uogonek uring utilde v w wacute wcircumflex wdieresis wgrave x y yacute ycircumflex ydieresis ydotbelow ygrave yhookabove ymacron ytilde z zacute zcaron zdotaccent jdotless.ss01 f_f f_f_i f_f_l fi fl ordfeminine ordmasculine florin florin.tf apostrophemod firsttonechinese dieresiscomb dieresiscomb.case dotaccentcomb dotaccentcomb.case gravecomb gravecomb.case acutecomb acutecomb.case hungarumlautcomb hungarumlautcomb.case caroncomb.alt circumflexcomb circumflexcomb.case circumflexcomb.loclVIT circumflexcomb.loclVIT.case caroncomb caroncomb.case brevecomb brevecomb.case ringcomb ringcomb.case tildecomb tildecomb.case macroncomb macroncomb.case dblgravecomb breveinvertedcomb breveinvertedcomb.case commaturnedabovecomb horncomb horncomb.case dotbelowcomb dieresisbelowcomb commaaccentcomb cedillacomb ogonekcomb brevebelowcomb macronbelowcomb acute breve caron cedilla circumflex dieresis dotaccent grave hungarumlaut macron ogonek ring tilde gravecomb.loclVIT gravecomb.loclVIT.case acutecomb.loclVIT acutecomb.loclVIT.case hookabovecomb hookabovecomb.case strokeshortcomb slashshortcomb brevecomb_acutecomb brevecomb_acutecomb.case brevecomb_gravecomb brevecomb_gravecomb.case brevecomb_tildecomb brevecomb_tildecomb.case circumflexcomb_acutecomb circumflexcomb_acutecomb.case circumflexcomb_gravecomb circumflexcomb_gravecomb.case circumflexcomb_hookabovecomb circumflexcomb_hookabovecomb.case circumflexcomb_tildecomb circumflexcomb_tildecomb.case')  # NoQA: E501
    print(a)
    print(a.write(), a.script)
