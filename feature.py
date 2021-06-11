__doc__ = """
A class to hold a single lookup.
"""

import re
import copy
from lookup import Lookup, LookupFlag, InFeatureClass
from substitution import Substitution


class Feature:
    def __init__(self, code=None, name=None):
        self.raw_code = code
        self.feature_code = code
        self.name = name
        self.code_sequence = []
        self.scripts = set()
        self.languages = set()

        # Conveniences
        self.all_glyphs = set()

        if code:
            self.parse_code()

    def __repr__(self):
        return '<OpentypeObject Feature \'{0}\' with {1} lookups covering scripts {2}>'.format(self.name, len(self.code_sequence), self.scripts)

    def __getitem__(self, i):
        return self.code_sequence[i]

    def parse_code(self):
        if self.name is None:
            try:
                parsed_code = re.search(r'feature (.+?) {(.+)}', self.raw_code, flags=re.DOTALL)
                self.name = parsed_code.group(1)
                self.feature_code = parsed_code.group(2)
            except AttributeError:
                print('Could not find a feature name in the code.')
                raise

        code_lines = [x.strip() for x in self.feature_code.split('\n') if x.strip()]

        current_script = None
        current_language = None

        i = 0
        while i < len(code_lines):
            line = code_lines[i].strip()

            # is a blank line
            if not line:
                i += 1
                continue

            # is a comment
            elif line.startswith('#'):
                obj = LookupFlag(line, script=current_script, language=current_language)

            # is a class defined within the feature
            elif line.startswith('@'):
                obj = InFeatureClass(line, script=current_script, language=current_language)
                self.all_glyphs.update(set(obj.members))

            # is a lookup definition
            elif line.startswith('lookup') and line.endswith('{'):
                lookup_name = re.search(r'lookup (.+?) {', line).group(1)
                lookup_end = None
                for li, l in enumerate(code_lines[i:]):
                    if re.search(r'}} ?{0}.*?;'.format(lookup_name), l):
                        lookup_end = li + i
                        break
                if lookup_end is None:
                    raise Exception

                lookup_text = '\n'.join(code_lines[i:lookup_end + 1])

                i = lookup_end
                obj = Lookup(lookup_text, script=current_script, language=current_language)

                self.all_glyphs.update(set(obj.all_glyphs))
                self.scripts.update(obj.scripts)
                self.languages.update(obj.languages)

                if current_script is not None and not obj.scripts:
                    obj.scripts = set([current_script])
                if current_language is not None and not obj.languages:
                    obj.languages = set([current_language])

            elif line.startswith('sub'):
                obj = Substitution(line, script=current_script, language=current_language)
                self.all_glyphs.update(set(obj.all_glyphs))

            else:
                obj = LookupFlag(line, script=current_script, language=current_language)
                if obj.script is not None:
                    self.scripts.add(obj.script)
                    current_script = obj.script
                    current_language = None
                elif current_script is not None:
                    obj.script = current_script

                if obj.language is not None and current_script is not None:
                    self.languages.add(obj.language)
                    current_language = obj.language
                    obj.script = current_script
                elif current_language is not None:
                    obj.language = current_language

                if obj.lookup_reference is not None:
                    for cso in self.code_sequence:
                        if isinstance(cso, Lookup):
                            if cso.name == obj.lookup_reference:
                                if current_script is not None:
                                    cso.scripts.add(current_script)
                                if current_language is not None:
                                    cso.languages.add(current_language)

            self.code_sequence.append(obj)

            i += 1

    def write(self, tab_level=0, **kwargs):
        if kwargs.get('omit_feature_declaration'):
            f_template = '{code}'
            tab_level = -1
        else:
            f_template = '{tab}feature {feature_name} {{\n{code}\n{tab}}} {feature_name};'

        code = '\n'.join(x.write(tab_level=tab_level + 1) if hasattr(x, 'write') else x for x in self.code_sequence)
        feature_text = f_template.format(
            feature_name=self.name,
            tab='\t' * tab_level,
            code=code
        )
        return feature_text

    def subset(self, scripts=None, languages=None, glyphs=None):
        new = copy.copy(self)
        if all([x is None for x in [scripts, languages, glyphs]]):
            return new

        new.code_sequence = []
        for x in self.code_sequence:
            new_x = x.subset(scripts=scripts, languages=languages, glyphs=glyphs)
            if new_x:
                new.code_sequence.append(new_x)

        # Check for any orphaned lookup references and replace them with the lookup definition.
        for i, x in enumerate(new.code_sequence):
            if not isinstance(x, LookupFlag):
                continue
            if x.lookup_reference:
                if not self.check_lookup_exists(new, x.lookup_reference):
                    for cso in self.code_sequence:
                        if isinstance(cso, Lookup) and cso.name == x.lookup_reference:
                            new.code_sequence[i] = copy.copy(cso)

        # Check to make sure a lookup or lookup reference is in the feature, otherwise the feature is redundant
        for x in new.code_sequence:
            if isinstance(x, LookupFlag):
                if x.lookup_reference:
                    return new

            if isinstance(x, Lookup):
                return new

            if isinstance(x, Substitution):
                return new

    @staticmethod
    def check_lookup_exists(feature, lookup_name):
        """
        Looks in the given feature to find the given lookup definition.
        """
        for x in feature:
            try:
                if x.name == lookup_name:
                    return True
            except AttributeError:
                continue

        return False


if __name__ == "__main__":
    x = Feature("""
lookup ccmp_Other_1 {
\t@CombiningTopAccents = [acutecomb brevecomb breveinvertedcomb caroncomb circumflexcomb commaturnedabovecomb dblgravecomb dieresiscomb dotaccentcomb gravecomb hungarumlautcomb macroncomb ringcomb tildecomb];  # NoQA: E501
\t@CombiningNonTopAccents = [brevebelowcomb cedillacomb dieresisbelowcomb dotbelowcomb macronbelowcomb ogonekcomb horncomb];
\tsub [i j]' @CombiningTopAccents by [idotless jdotless];
\tsub [i j]' @CombiningNonTopAccents @CombiningTopAccents by [idotless jdotless];
\t@Markscomb = [circumflexcomb.loclVIT breveinvertedcomb horncomb dieresis dotaccent grave acute hungarumlaut circumflex caron breve ring tilde macron brevecomb_acutecomb brevecomb_gravecomb brevecomb_tildecomb circumflexcomb_acutecomb circumflexcomb_gravecomb circumflexcomb_hookabovecomb circumflexcomb_tildecomb];
\t@MarkscombCase = [circumflexcomb.loclVIT.case breveinvertedcomb.case horncomb.case dieresiscomb.case dotaccentcomb.case gravecomb.case acutecomb.case hungarumlautcomb.case circumflexcomb.case caroncomb.case brevecomb.case ringcomb.case tildecomb.case macroncomb.case brevecomb_acutecomb.case brevecomb_gravecomb.case brevecomb_tildecomb.case circumflexcomb_acutecomb.case circumflexcomb_gravecomb.case circumflexcomb_hookabovecomb.case circumflexcomb_tildecomb.case];
\tsub @Markscomb @Markscomb' by @MarkscombCase;
\tsub @Uppercase @Markscomb' by @MarkscombCase;
} ccmp_Other_1;

lookup ccmp_Other_2 {
\tsub @Markscomb' @MarkscombCase by @MarkscombCase;
\tsub @MarkscombCase @Markscomb' by @MarkscombCase;
} ccmp_Other_2;

lookup ccmp_latn_1 {
\tlookupflag 0;
\tsub brevecomb acutecomb by brevecomb_acutecomb;
\tsub brevecomb gravecomb by brevecomb_gravecomb;
\tsub brevecomb tildecomb by brevecomb_tildecomb;
\tsub circumflexcomb acutecomb by circumflexcomb_acutecomb;
\tsub circumflexcomb gravecomb by circumflexcomb_gravecomb;
\tsub circumflexcomb tildecomb by circumflexcomb_tildecomb;
} ccmp_latn_1;

script latn;
lookup ccmp_latn_1;

script dev2;
lookup ccmap1 {
\tsub eCandraMatra-deva anusvara-deva by candraBindu-deva;
\tsub danda-deva danda-deva by dbldanda-deva;
} ccmap1;

language MAR;
lookup ccmap1;

script deva;
lookup ccmap1;

language MAR;
lookup ccmap1;
""", 'ccmp')

    f = x
    # print('name:', f.name)
    # print('all_glyphs:', f.all_glyphs)
    # print('scripts:', f.scripts)
    # print('code_sequence:', f.code_sequence)
    for cs0 in f.code_sequence:
        if isinstance(cs0, LookupFlag):
            print(cs0, cs0.script, cs0.language, cs0.is_lookupflag)
        else:
            try:
                print(cs0, cs0.script, cs0.language)
            except AttributeError:
                print(cs0, cs0.scripts, cs0.languages)
    # subst = f.subset(scripts=['latn', None], glyphs='A Aacute Abreve Abreveacute Abrevedotbelow Abrevegrave Abrevehookabove Abrevetilde Acircumflex Acircumflexacute Acircumflexdotbelow Acircumflexgrave Acircumflexhookabove Acircumflextilde Adblgrave Adieresis Adotbelow Agrave Ahookabove Ainvertedbreve Amacron Aogonek Aring Aringacute Atilde AE AEacute B C Cacute Ccaron Ccedilla Ccircumflex Cdotaccent D DZcaron Eth Dcaron Dcroat Dzcaron E Eacute Ebreve Ecaron Ecircumflex Ecircumflexacute Ecircumflexdotbelow Ecircumflexgrave Ecircumflexhookabove Ecircumflextilde Edblgrave Edieresis Edotaccent Edotbelow Egrave Ehookabove Einvertedbreve Emacron Eogonek Etilde F G Gbreve Gcaron Gcircumflex Gcommaaccent Gdotaccent H Hbar Hcircumflex I IJ Iacute Ibreve Icircumflex Idblgrave Idieresis Idotaccent Idotbelow Igrave Ihookabove Iinvertedbreve Imacron Iogonek Itilde J Jcircumflex K Kcommaaccent L LJ Lacute Lcaron Lcommaaccent Ldot Lj Lslash M N NJ Nacute Ncaron Ncommaaccent Eng Nj Ntilde O Oacute Obreve Ocircumflex Ocircumflexacute Ocircumflexdotbelow Ocircumflexgrave Ocircumflexhookabove Ocircumflextilde Odblgrave Odieresis Odieresismacron Odotaccentmacron Odotbelow Ograve Ohookabove Ohorn Ohornacute Ohorndotbelow Ohorngrave Ohornhookabove Ohorntilde Ohungarumlaut Oinvertedbreve Omacron Oogonek Oslash Oslashacute Otilde Otildemacron OE P Thorn Q R Racute Rcaron Rcommaaccent Rdblgrave Rinvertedbreve S Sacute Scaron Scedilla Scircumflex Scommaaccent Germandbls Schwa T Tbar Tcaron Tcedilla Tcommaaccent U Uacute Ubreve Ucircumflex Udblgrave Udieresis Udotbelow Ugrave Uhookabove Uhorn Uhornacute Uhorndotbelow Uhorngrave Uhornhookabove Uhorntilde Uhungarumlaut Uinvertedbreve Umacron Uogonek Uring Utilde V W Wacute Wcircumflex Wdieresis Wgrave X Y Yacute Ycircumflex Ydieresis Ydotbelow Ygrave Yhookabove Ymacron Ytilde Z Zacute Zcaron Zdotaccent a aacute abreve abreveacute abrevedotbelow abrevegrave abrevehookabove abrevetilde acircumflex acircumflexacute acircumflexdotbelow acircumflexgrave acircumflexhookabove acircumflextilde adblgrave adieresis adotbelow agrave ahookabove ainvertedbreve amacron aogonek aring aringacute atilde ae aeacute b c cacute ccaron ccedilla ccircumflex cdotaccent d eth eth.ss01 dcaron dcroat dzcaron e eacute ebreve ecaron ecircumflex ecircumflexacute ecircumflexdotbelow ecircumflexgrave ecircumflexhookabove ecircumflextilde edblgrave edieresis edotaccent edotbelow egrave ehookabove einvertedbreve emacron eogonek etilde schwa f g gbreve gcaron gcircumflex gcommaaccent gdotaccent h hbar hcircumflex i idotless iacute ibreve icircumflex idblgrave idieresis idotaccent idotbelow igrave ihookabove iinvertedbreve ij imacron iogonek itilde j jdotless jcircumflex k kcommaaccent kgreenlandic l lacute lcaron lcommaaccent ldot lj lslash m n nacute napostrophe ncaron ncommaaccent eng nj ntilde o oacute obreve ocircumflex ocircumflexacute ocircumflexdotbelow ocircumflexgrave ocircumflexhookabove ocircumflextilde odblgrave odieresis odieresismacron odotaccentmacron odotbelow ograve ohookabove ohorn ohornacute ohorndotbelow ohorngrave ohornhookabove ohorntilde ohungarumlaut oinvertedbreve omacron oogonek oslash oslashacute otilde otildemacron oe p thorn q r racute rcaron rcommaaccent rdblgrave rinvertedbreve s sacute scaron scedilla scircumflex scommaaccent germandbls t tbar tcaron tcedilla tcommaaccent u uacute ubreve ucircumflex udblgrave udieresis udotbelow ugrave uhookabove uhorn uhornacute uhorndotbelow uhorngrave uhornhookabove uhorntilde uhungarumlaut uinvertedbreve umacron uogonek uring utilde v w wacute wcircumflex wdieresis wgrave x y yacute ycircumflex ydieresis ydotbelow ygrave yhookabove ymacron ytilde z zacute zcaron zdotaccent jdotless.ss01 f_f f_f_i f_f_l fi fl ordfeminine ordmasculine florin florin.tf apostrophemod firsttonechinese dieresiscomb dieresiscomb.case dotaccentcomb dotaccentcomb.case gravecomb gravecomb.case acutecomb acutecomb.case hungarumlautcomb hungarumlautcomb.case caroncomb.alt circumflexcomb circumflexcomb.case circumflexcomb.loclVIT circumflexcomb.loclVIT.case caroncomb caroncomb.case brevecomb brevecomb.case ringcomb ringcomb.case tildecomb tildecomb.case macroncomb macroncomb.case dblgravecomb breveinvertedcomb breveinvertedcomb.case commaturnedabovecomb horncomb horncomb.case dotbelowcomb dieresisbelowcomb commaaccentcomb cedillacomb ogonekcomb brevebelowcomb macronbelowcomb acute breve caron cedilla circumflex dieresis dotaccent grave hungarumlaut macron ogonek ring tilde gravecomb.loclVIT gravecomb.loclVIT.case acutecomb.loclVIT acutecomb.loclVIT.case hookabovecomb hookabovecomb.case strokeshortcomb slashshortcomb brevecomb_acutecomb brevecomb_acutecomb.case brevecomb_gravecomb brevecomb_gravecomb.case brevecomb_tildecomb brevecomb_tildecomb.case circumflexcomb_acutecomb circumflexcomb_acutecomb.case circumflexcomb_gravecomb circumflexcomb_gravecomb.case circumflexcomb_hookabovecomb circumflexcomb_hookabovecomb.case circumflexcomb_tildecomb circumflexcomb_tildecomb.case')  # NoQA: E501
    # subst = f.subset(scripts=['deva', 'dev2', None], glyphs='rephmatra-deva rekha aShort-deva aCandra-deva a-deva aa-deva i-deva ii-deva u-deva uu-deva rVocalic-deva rrVocalic-deva lVocalic-deva llVocalic-deva eCandra-deva eShort-deva e-deva ai-deva oCandra-deva oShort-deva o-deva au-deva oe-deva ooe-deva aw-deva ue-deva uue-deva aaMatra-deva iMatra-deva iMatra_anusvara-deva iMatra_reph-deva iMatra_reph_anusvara-deva iiMatra-deva iiMatra_reph-deva iiMatra_reph_anusvara-deva oCandraMatra-deva oShortMatra-deva oMatra-deva oMatra_reph-deva oMatra_reph_anusvara-deva auMatra-deva auMatra_reph-deva auMatra_reph_anusvara-deva prishthaMatraE-deva ooeMatra-deva awMatra-deva marwaridda-deva ka-deva kha-deva kha-deva.ss02 ga-deva gha-deva nga-deva ca-deva cha-deva ja-deva ja-deva.ss02 jha-deva nya-deva tta-deva ttha-deva dda-deva ddha-deva nna-deva ta-deva tha-deva da-deva dha-deva na-deva nnna-deva pa-deva pha-deva ba-deva bha-deva ma-deva ya-deva ra-deva rra-deva la-deva la-deva.loclMAR lla-deva llla-deva va-deva sha-deva sha-deva.loclMAR ssa-deva sa-deva ha-deva qa-deva khha-deva ghha-deva za-deva dddha-deva rha-deva fa-deva yya-deva zha-deva jjya-deva gga-deva jja-deva ddda-deva bba-deva dddh_ra-deva dddh_rakar-deva k_ka-deva k_kha-deva k_ca-deva k_ja-deva k_tta-deva k_nna-deva k_ta-deva k_ta-deva.trad k_t-deva k_t_ta-deva k_t_ya-deva k_t_ra-deva k_t_va-deva k_tha-deva k_da-deva k_na-deva k_pa-deva k_p_ra-deva k_pha-deva k_ma-deva k_ya-deva k_ra-deva k_la-deva k_va-deva k_v_ya-deva k_sha-deva k_ssa-deva k_ss-deva k_ss_ma-deva k_ss_ya-deva k_ss_ra-deva k_ss_va-deva k_sa-deva k_s_tta-deva k_s_dda-deva k_s_ta-deva k_s_pa-deva k_s_p_ra-deva k_s_p_la-deva k_rakar-deva kh_kha-deva kh_ta-deva kh_na-deva kh_ma-deva kh_ya-deva kh_ra-deva kh_va-deva kh_sha-deva kh_rakar-deva g_ga-deva g_gha-deva g_ja-deva g_nna-deva g_da-deva g_dha-deva g_dh_ya-deva g_dh_va-deva g_na-deva g_n_ya-deva g_ba-deva g_bha-deva g_bh_ya-deva g_ma-deva g_ya-deva g_ra-deva g_la-deva g_va-deva g_sa-deva g_rakar-deva g_r_ya-deva gh_na-deva gh_ma-deva gh_ya-deva gh_ra-deva gh_rakar-deva ng_ra-deva c_ca-deva c_cha-deva c_ch_va-deva c_na-deva c_ma-deva c_ya-deva c_ra-deva c_rakar-deva ch_na-deva ch_na-deva.trad ch_ya-deva ch_ra-deva ch_va-deva j_ka-deva j_ja-deva j_j_nya-deva j_j_ya-deva j_j_va-deva j_jha-deva j_nya-deva j_ny-deva j_ny_ya-deva j_tta-deva j_dda-deva j_ta-deva j_da-deva j_na-deva j_ba-deva j_ma-deva j_ya-deva j_ra-deva j_va-deva j_rakar-deva jh_na-deva jh_ma-deva jh_ya-deva jh_ra-deva jh_rakar-deva ny_ca-deva ny_c_ya-deva ny_cha-deva ny_ja-deva ny_j_ya-deva ny_ra-deva ny_sha-deva ny_rakar-deva tt_tta-deva tt_tt_ya-deva tt_ttha-deva tt_ddha-deva tt_na-deva tt_na-deva.trad tt_ya-deva tt_ra-deva tt_va-deva tt_sa-deva tth_ttha-deva tth_tth_ya-deva tth_na-deva tth_na-deva.trad tth_ya-deva tth_ra-deva dd_gha-deva dd_tta-deva dd_dda-deva dd_dd_ya-deva dd_ddha-deva dd_na-deva dd_na-deva.trad dd_ma-deva dd_ya-deva dd_ra-deva ddh_ddha-deva ddh_ddh_ya-deva ddh_na-deva ddh_na-deva.trad ddh_ya-deva ddh_ra-deva nn_tta-deva nn_ttha-deva nn_dda-deva nn_ddha-deva nn_nna-deva nn_ma-deva nn_ya-deva nn_ra-deva nn_va-deva nn_rakar-deva t_ka-deva t_k_ya-deva t_k_ra-deva t_k_va-deva t_k_ssa-deva t_k_rakar-deva t_kha-deva t_kh_na-deva t_kh_ra-deva t_ta-deva t_t-deva t_t_ya-deva t_t_va-deva t_tha-deva t_na-deva t_na-deva.trad t_n_ya-deva t_pa-deva t_p_ra-deva t_p_la-deva t_p_rakar-deva t_pha-deva t_ma-deva t_m_ya-deva t_ya-deva t_ra-deva t_la-deva t_va-deva t_sa-deva t_s_na-deva t_s_ya-deva t_s_va-deva t_rakar-deva t_r_ya-deva th_na-deva th_ya-deva th_ra-deva th_va-deva th_rakar-deva d_ga-deva d_g_ra-deva d_gha-deva d_da-deva d_d_ya-deva d_dha-deva d_na-deva d_ba-deva d_b_ra-deva d_bha-deva d_ma-deva d_ya-deva d_ra-deva d_va-deva d_v_ra-deva d_rakar-deva d_r_ya-deva dh_na-deva dh_n_ya-deva dh_ma-deva dh_ya-deva dh_ra-deva dh_va-deva dh_rakar-deva n_ka-deva n_k_sa-deva n_ca-deva n_tta-deva n_dda-deva n_ta-deva n_t_ya-deva n_t_ra-deva n_t_sa-deva n_t_rakar-deva n_tha-deva n_th_ya-deva n_th_va-deva n_da-deva n_d_ra-deva n_d_va-deva n_dha-deva n_dh_ya-deva n_dh_ra-deva n_dh_va-deva n_dh_rakar-deva n_na-deva n_n-deva n_n_ya-deva n_pa-deva n_p_ra-deva n_p_rakar-deva n_pha-deva n_bha-deva n_ma-deva n_m_ya-deva n_ya-deva n_ra-deva n_va-deva n_sa-deva n_s_tta-deva n_ha-deva n_h_ya-deva n_rakar-deva nnn_ra-deva p_tta-deva p_tta-deva.trad p_ta-deva p_t_ya-deva p_na-deva p_pa-deva p_pha-deva p_ma-deva p_ya-deva p_ra-deva p_la-deva p_va-deva p_sa-deva p_rakar-deva ph_ja-deva ph_tta-deva ph_ta-deva ph_na-deva ph_pa-deva ph_pha-deva ph_ya-deva ph_ra-deva ph_la-deva ph_sha-deva ph_rakar-deva b_ja-deva b_j_ya-deva b_ta-deva b_da-deva b_dha-deva b_dh_va-deva b_na-deva b_ba-deva b_bha-deva b_bh_ra-deva b_bh_rakar-deva b_ya-deva b_ra-deva b_la-deva b_l_ya-deva b_va-deva b_sha-deva b_sa-deva b_za-deva b_rakar-deva bh_na-deva bh_ya-deva bh_ra-deva bh_va-deva bh_rakar-deva bh_r_ya-deva m_ta-deva m_da-deva m_na-deva m_pa-deva m_p_ra-deva m_p_rakar-deva m_ba-deva m_b_ya-deva m_b_ra-deva m_b_rakar-deva m_bha-deva m_bh_ra-deva m_bh_rakar-deva m_ma-deva m_ya-deva m_ra-deva m_la-deva m_va-deva m_sha-deva m_sa-deva m_ha-deva m_rakar-deva y_na-deva y_ya-deva y_ra-deva y_rakar-deva rr_ya-deva rr_ha-deva l_ka-deva l_k_ya-deva l_kha-deva l_ga-deva l_ja-deva l_tta-deva l_ttha-deva l_dda-deva l_ddha-deva l_ta-deva l_tha-deva l_th_ya-deva l_da-deva l_d_ra-deva l_pa-deva l_pha-deva l_ba-deva l_bha-deva l_ma-deva l_ya-deva l_ra-deva l_la-deva l_l_ya-deva l_va-deva l_v_dda-deva l_sa-deva l_ha-deva l_h_ya-deva l_za-deva l_rakar-deva ll_ya-deva ll_ra-deva ll_rakar-deva lll_ra-deva lll_rakar-deva v_na-deva v_ya-deva v_ra-deva v_la-deva v_va-deva v_ha-deva v_rakar-deva sh_ka-deva sh_ca-deva sh_cha-deva sh_tta-deva sh_ta-deva sh_na-deva sh_ma-deva sh_ya-deva sh_ra-deva sh_la-deva sh_va-deva sh_sha-deva sh_qa-deva sh_rakar-deva sh_r_ya-deva ss_ka-deva ss_k_ra-deva ss_tta-deva ss_tta-deva.trad ss_tt_ya-deva ss_tt_ya-deva.trad ss_tt_va-deva ss_tt_rakar-deva ss_ttha-deva ss_ttha-deva.trad ss_tth_ya-deva ss_tth_ya-deva.trad ss_tth_rakar-deva ss_nna-deva ss_nn_ya-deva ss_pa-deva ss_p_ra-deva ss_p_rakar-deva ss_pha-deva ss_ma-deva ss_m_ya-deva ss_ya-deva ss_ra-deva ss_va-deva ss_ssa-deva ss_rakar-deva s_ka-deva s_k_ra-deva s_k_va-deva s_kha-deva s_ja-deva s_tta-deva s_ta-deva s_t_ya-deva s_t_ra-deva s_t_va-deva s_tha-deva s_th_ya-deva s_da-deva s_na-deva s_pa-deva s_p_ra-deva s_pha-deva s_ba-deva s_ma-deva s_m_ya-deva s_ya-deva s_ra-deva s_la-deva s_va-deva s_sa-deva s_rakar-deva h_nna-deva h_na-deva h_ma-deva h_ya-deva h_ra-deva h_la-deva h_va-deva q_ta-deva q_pha-deva q_ba-deva q_ma-deva q_ra-deva q_qa-deva q_fa-deva q_rakar-deva khh_ta-deva khh_ma-deva khh_ya-deva khh_ra-deva khh_va-deva khh_sha-deva khh_sa-deva khh_rakar-deva ghh_ra-deva ghh_rakar-deva z_ya-deva z_ra-deva z_za-deva z_rakar-deva f_ta-deva f_ra-deva f_sa-deva f_za-deva f_fa-deva f_rakar-deva yy_ra-deva yy_rakar-deva rh_ra-deva rh_rakar-deva ng_ka-deva ng_k_ra-deva ng_ga-deva ng_g_ra-deva h_m_ya-deva dddh-deva k-deva kh-deva g-deva gh-deva c-deva ch-deva j-deva jh-deva ny-deva nn-deva t-deva th-deva d-deva d_rVocalicMatra-deva dh-deva n-deva nnn-deva p-deva ph-deva b-deva bh-deva m-deva y-deva ra_uMatra-deva ra_uuMatra-deva rr-deva l-deva l-deva.loclMAR ll-deva lll-deva v-deva sh-deva sh-deva.loclMAR ss-deva s-deva ha_rVocalicMatra-deva h-deva q-deva khh-deva ghh-deva z-deva f-deva yy-deva rh-deva zero-deva zero-deva.tf one-deva one-deva.tf two-deva two-deva.tf three-deva three-deva.tf four-deva four-deva.tf five-deva five-deva.tf six-deva six-deva.tf seven-deva seven-deva.tf eight-deva eight-deva.tf nine-deva nine-deva.tf glottalstop-deva danda-deva dbldanda-deva abbreviation-deva highspacingdot-deva avagraha-deva om-deva apostrophemod firsttonechinese dieresiscomb dieresiscomb.case dotaccentcomb dotaccentcomb.case gravecomb gravecomb.case acutecomb acutecomb.case hungarumlautcomb hungarumlautcomb.case caroncomb.alt circumflexcomb circumflexcomb.case circumflexcomb.loclVIT circumflexcomb.loclVIT.case caroncomb caroncomb.case brevecomb brevecomb.case ringcomb ringcomb.case tildecomb tildecomb.case macroncomb macroncomb.case dblgravecomb breveinvertedcomb breveinvertedcomb.case commaturnedabovecomb horncomb horncomb.case dotbelowcomb dieresisbelowcomb commaaccentcomb cedillacomb ogonekcomb brevebelowcomb macronbelowcomb acute breve caron cedilla circumflex dieresis dotaccent grave hungarumlaut macron ogonek ring tilde gravecomb.loclVIT gravecomb.loclVIT.case acutecomb.loclVIT acutecomb.loclVIT.case hookabovecomb hookabovecomb.case strokeshortcomb slashshortcomb uMatra-deva uMatra-deva.small uuMatra-deva rVocalicMatra-deva rrVocalicMatra-deva lVocalicMatra-deva llVocalicMatra-deva eCandraMatra-deva candraBindu-deva invertedCandraBindu-deva eShortMatra-deva eMatra-deva eMatra_anusvara-deva eMatra_reph-deva eMatra_reph_anusvara-deva aiMatra-deva aiMatra_anusvara-deva aiMatra_reph-deva aiMatra_reph_anusvara-deva anusvara-deva visarga-deva halant-deva nukta-deva reph-deva reph_candra-deva reph_candraBindu-deva reph_anusvara-deva reph_udatta-deva rakar-deva rakar_uMatra-deva rakar_uuMatra-deva eLongCandra-deva oeMatra-deva ueMatra-deva uueMatra-deva udatta-deva anudatta-deva grave-deva acute-deva')  # NoQA: E501
    subst = f.subset(scripts=['guru', None], glyphs='aaMatra-gurmukhi iMatra-gurmukhi iiMatra-gurmukhi a-gurmukhi aa-gurmukhi i-gurmukhi ii-gurmukhi u-gurmukhi uu-gurmukhi ee-gurmukhi ai-gurmukhi oo-gurmukhi au-gurmukhi ka-gurmukhi kha-gurmukhi ga-gurmukhi gha-gurmukhi nga-gurmukhi ca-gurmukhi cha-gurmukhi ja-gurmukhi jha-gurmukhi nya-gurmukhi tta-gurmukhi ttha-gurmukhi dda-gurmukhi ddha-gurmukhi nna-gurmukhi ta-gurmukhi tha-gurmukhi da-gurmukhi dha-gurmukhi na-gurmukhi pa-gurmukhi pha-gurmukhi ba-gurmukhi bha-gurmukhi ma-gurmukhi ya-gurmukhi ya-gurmukhi.post ra-gurmukhi la-gurmukhi lla-gurmukhi va-gurmukhi sha-gurmukhi sa-gurmukhi ha-gurmukhi khha-gurmukhi ghha-gurmukhi za-gurmukhi rra-gurmukhi fa-gurmukhi iri-gurmukhi ura-gurmukhi ekonkar-gurmukhi zero-gurmukhi zero-gurmukhi.tf one-gurmukhi one-gurmukhi.tf two-gurmukhi two-gurmukhi.tf three-gurmukhi three-gurmukhi.tf four-gurmukhi four-gurmukhi.tf five-gurmukhi five-gurmukhi.tf six-gurmukhi six-gurmukhi.tf seven-gurmukhi seven-gurmukhi.tf eight-gurmukhi eight-gurmukhi.tf nine-gurmukhi nine-gurmukhi.tf space nbspace zerowidthjoiner zerowidthnonjoiner .notdef CR NULL zeroWidthNoBreakSpace apostrophemod firsttonechinese dieresiscomb dieresiscomb.case dotaccentcomb dotaccentcomb.case gravecomb gravecomb.case acutecomb acutecomb.case hungarumlautcomb hungarumlautcomb.case caroncomb.alt circumflexcomb circumflexcomb.case circumflexcomb.loclVIT circumflexcomb.loclVIT.case caroncomb caroncomb.case brevecomb brevecomb.case ringcomb ringcomb.case tildecomb tildecomb.case macroncomb macroncomb.case dblgravecomb breveinvertedcomb breveinvertedcomb.case commaturnedabovecomb horncomb horncomb.case dotbelowcomb dieresisbelowcomb commaaccentcomb cedillacomb ogonekcomb brevebelowcomb macronbelowcomb acute breve caron cedilla circumflex dieresis dotaccent grave hungarumlaut macron ogonek ring tilde gravecomb.loclVIT gravecomb.loclVIT.case acutecomb.loclVIT acutecomb.loclVIT.case hookabovecomb hookabovecomb.case strokeshortcomb slashshortcomb adakbindi-gurmukhi bindi-gurmukhi visarga-gurmukhi nukta-gurmukhi ra-gurmukhi.below uMatra-gurmukhi uuMatra-gurmukhi eeMatra-gurmukhi aiMatra-gurmukhi ooMatra-gurmukhi auMatra-gurmukhi halant-gurmukhi udaat-gurmukhi tippi-gurmukhi addak-gurmukhi yakash-gurmukhi ha-gurmukhi.below va-gurmukhi.below')  # NoQA: E501
    print('\nSubset:')
    if subst:
        print(subst.write())
