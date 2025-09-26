#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Convert ICOS variables and ICOS units into LaTeX-snippets. 
    For details on LaTeX we refer to
        https://www.ctan.org/tex-archive/info/lshort/english/

    The implementation is directed towards javascript applications.

        (***) Warning:
        --------------
        Regarding the size commands, they *should* not be used in math
        mode. Compiling ${\small {x}}$ (outside python) yields a LaTeX-
        warning. A correct LaTeX-string would be \small{$x$}.
        A guess is that MathJax (a javascript interpreter for LaTeX, mathML
        and AsciiMath - see mathjax.org), expects all LaTeX-code to be
        within $-signs.
        At least plotly use mathjax, while e.g. matplotlib use either mathjax or
        compiled images.
        -- Thus, if by some reason code compilation fails, try to set
        font_size = 0 in your call.

    Examples
    --------
    >>>import eco_tool.icos2latex
    >>>lat = icos2latex.Translator()
    >>>lat.var_unit_to_latex(('CO2','µmol mol-1'))
    '${CO_2}\ (\mu{mol}/{mol})$'

    >>>lat = icos2latex.Translator(font_size = 10)
    >>>lat.var_to_latex('CO2')
    '${\\small  {CO_2}}$'

    >>>lat = icos2latex.Translator(font_style = 'sans')
    >>>lat.unit_to_latex('nmol mol-1')
    '${\\mathrm  {{nmol}/{mol}}}$'

    >>>lat = icos2latex.Translator(use_exp=False)
    >>>lat.unit_to_latex('nmol mol-1')
    '${nmol}/{mol}$'
    
    >>>lat = icos2latex.Translator(use_exp=True, font_size=10, font_style='tt')
    >>>lat.var_unit_to_latex(('CO2','µmol mol-1'))
    '${\\small  {\\mathtt  {{CO_2}\\ (\\mu{mol}\\,\\,{mol}^{-1})}}}$'

"""

__author__ = ["Anders Dahlner"]
__credits__ = "ICOS Carbon Portal"
__license__ = "GPLv3+"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, Elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']


class Translator:
    # We use some class members in order to improve
    # the performance reasons. These are all private.
    __layout = {
        'font_size': {
            'Default': None,
            'None': None,            # default latex style
            '6': r'\tiny ',          # ~6pt
            '8': r'\scriptsize ',    # ~8pt, *default
            '9': r'\footnotesize ',  # ~9pt
            '10': r'\small ',        # ~10pt
            '11': r'\normalsize ',   # ...
            '12': r'\large ',
            '14': r'\Large ',
            '17': r'\LARGE ',
            '21': r'\huge ',
            '25': r'\Huge '},
        # see (***) above
        'font_style': {
            'Default': None,    # *default
            'None': None,
            'rm': r'\mathrm ',  # serif, ~times roman,
            'sf': r'\mathsf ',  # sans-serif, no serifs, web-text
            'tt': r'\mathtt ',  # serif, typewriter text
            'it': r'\mathit ',  # serif, italic, ~ like default latex
            'bf': r'\mathbf ',  # serif, bold
            'bb': r'\mathbb ',  # black-board bold, for capitals
            'cal': r'\mathcal ',  # calligraphy, for capitals
            'frak': r'\mathfrak '  # fraktur, for capitals
            },  # default latex style
        'use_exp': False}   # Applies to units, if True output
    # will use negative exponents instead of
    # div-signs. e.g 'm/s' or m s^{-1}

    @classmethod
    def __var_to_latex(cls, var: str = None):
        """ 
        Converts ICOS-variables to latex-strings.

        Parameters
        ----------
        var: str
            Expects a string having the format of an ICOS-variable
            (see the formats below)

        Returns
        -------
        str 
        """
        # ICOS var and units:
        # AS :  {('AP', 'hPa'), ('AP-Flag', 'No unit'), ('AP-NbPoints', 'No unit'),
        #        ('AP-Stdev', 'hPa'), ('AT', '°C'), ('AT-Flag', 'No unit'),
        #        ('AT-NbPoints', 'No unit'), ('AT-Stdev', '°C'), ('Flag', 'No unit'),
        #        ('NbPoints', 'No unit'), ('RH', '%'), ('RH-Flag', 'No unit'),
        #        ('RH-NbPoints', 'No unit'), ('RH-Stdev', '%'), ('Stdev', 'nmol mol-1'),
        #        ('TIMESTAMP', 'No unit'), ('WD', '°'), ('WD-Flag', 'No unit'),
        #        ('WD-NbPoints', 'No unit'), ('WD-Stdev', '°'), ('WS', 'm s-1'),
        #        ('WS-Flag', 'No unit'), ('WS-NbPoints', 'No unit'),
        #        ('WS-Stdev', 'm s-1'), ('ch4', 'nmol mol-1'), ('co', 'nmol mol-1'),
        #        ('co2', 'µmol mol-1'), ('n2o', 'nmol mol-1'), ('rn', 'Bq m-3')}
        # OS :  {('Atmospheric Pressure [hPa]', 'hPa'), ('Atmospheric Pressure [hPa] QC Flag', 'No unit'),
        #        ('Latitude', '°'), ('Longitude', '°'), ('P_sal [psu]', 'psu'),
        #        ('P_sal [psu] QC Flag', 'No unit'), ('QC Flag', 'No unit'),
        #        ('TIMESTAMP', 'No unit'), ('Temp [degC]', '°C'), ('Temp [degC] QC Flag', 'No unit'),
        #        ('fCO2 [uatm]', 'µatm'), ('fCO2 [uatm] QC Flag', 'No unit'),
        #        ('fCO2 in atmosphere [uatm]', 'µatm'), ('fCO2 in atmosphere [uatm] QC Flag', 'No unit'),
        #        ('pCO2 [uatm]', 'µatm'), ('pCO2 [uatm] QC Flag', 'No unit'),
        #        ('pCO2 in atmosphere [uatm]', 'µatm'), ('pCO2 in atmosphere [uatm] QC Flag', 'No unit')})
        # ES :  {('CO2', 'µmol mol-1'), ('D_SNOW', 'cm'), ('D_SNOW_1_1_1', 'cm'), ...,
        #        ('FC', 'µmol m-2 s-1'), ('G_1', 'W m-2'), ('G_10_1_1', 'W m-2'), ...
        #        ('H', 'W m-2'), ('H2O', 'mmol mol-1'), ('H_UNCLEANED', 'W m-2'), ('LE', 'W m-2'),
        #        ('LE_UNCLEANED', 'W m-2'), ('LW_IN', 'W m-2'), ('LW_IN_1_1_1', 'W m-2'), ...
        #        ('LW_OUT', 'W m-2'), ('LW_OUT_1_1_1', 'W m-2'), ('LW_OUT_1_1_2', 'W m-2'),
        #        ('NEE', 'µmol m-2 s-1'), ('NEE_UNCLEANED', 'µmol m-2 s-1'), ('P', 'mm'),
        #        ('PA', 'kPa'), ('PA_1_1_1', 'kPa'), ...
        #        ('PPFD_BC_IN', 'µmol m-2 s-1'), ('PPFD_BC_IN_1', 'µmol m-2 s-1'), ...
        #        ('PPFD_BC_IN_10_1_1', 'µmol m-2 s-1'), ...
        #        ('PPFD_DIF', 'µmol m-2 s-1'), ('PPFD_DIF_1_1_1', 'µmol m-2 s-1'), ...
        #        ('PPFD_IN', 'µmol m-2 s-1'), ('PPFD_IN_1_1_1', 'µmol m-2 s-1'), ...
        #        ('PPFD_OUT', 'µmol m-2 s-1'), ('PPFD_OUT_1_1_1', 'µmol m-2 s-1'), ...
        #        ('P_12_1_1', 'mm'), ...
        #        ('RH', '%'), ('RH_1', '%'), ('RH_10', '%'),...
        #        ('RH_1_10_1', '%'), ...
        #        ('SC', 'µmol m-2 s-1'), ('SG_10_1_1', 'W m-2'), ...
        #        ('SWC_1', '%'), ('SWC_10', '%'), ('SWC_10_1_1', '%'), ...
        #        ('SW_DIF', 'W m-2'), ('SW_DIF_1_1_1', 'W m-2'), ('SW_IN', 'W m-2'), ('SW_IN_1_1_1', 'W m-2'),...
        #        ('SW_OUT', 'W m-2'), ('SW_OUT_1_1_1', 'W m-2'), ...
        #        ('TA', '°C'), ('TAU', 'kg m-1 s-2'), ('TA_1', '°C'),...
        #        ('TA_1_10_1', '°C'), ...
        #        ('TIMESTAMP', 'No unit'), ('TIMESTAMP_END', 'No unit'), ...
        #        ('TS_1', '°C'), ('TS_10_1_1', '°C'),...
        #        ('USTAR', 'm s-1'), ('VPD', 'hPa'), ('VPD_1', 'hPa'), ('VPD_10', 'hPa'),...
        #        ('VPD_1_10_1', 'hPa'), ('VPD_1_11_1', 'hPa'),...
        #        ('WD', '°'), ('WD_1', '°'), ('WD_1_1_1', '°'), ('WD_1_1_2', '°'),...
        #        ('WS', 'm s-1'), ('WS_1', 'm s-1'), ('WS_1_1_1', 'm s-1'), ...
        #        ('WTD', 'm'), ('WTD_10_1_1', 'm'), ('WTD_11_1_1', 'm'), ...
        #        ('W_SIGMA', 'm s-1'), ('ZL', 'No unit')}

        if not isinstance(var, str):
            return ''

        trans_dict = {'IN': r'{\mathit{IN}}',
                      'OUT': r'{\mathit{OUT}}',
                      'CO2': r'CO_2',
                      'co2': r'CO_2',
                      'fCO2': r'fCO_2',
                      'pCO2': r'pCO_2',
                      'co': r'CO',
                      'ch4': r'CH_4',
                      'H2O': r'H_2O',
                      'n2o': r'N_2O',
                      'SIGMA': r'{\sigma}',
                      'rn': r'RN',
                      'UNCLEANED': r'{\mathit{UNCLEANED}}',
                      '[degC]': r'[^{\circ}C]',
                      '[uatm]': r'[\mu {atm}]'}

        var_ls = var.split(' ')
        latex_ls = []
        var_word_ls = []

        for word in var_ls:
            word_parts = word.split('_')
            latex_parts = []
            while word_parts:
                word_part = word_parts.pop(0)
                if word_part in trans_dict.keys():
                    tex_txt = f'{{{trans_dict[word_part]}}}'
                elif word_part.isdigit():
                    digit_ls = [word_part]
                    while word_parts and word_parts[0].isdigit():
                        digit_ls.append(word_parts.pop(0))
                    if len(digit_ls) == 1:
                        tex_txt = f'*{{{digit_ls[0]}}}'
                    else:
                        digits = ','.join(digit_ls)
                        tex_txt = f'*{{({digits})}}'
                else:
                    tex_txt = f'{{{word_part}}}'

                latex_parts.append(tex_txt)

            if latex_parts:
                latex_part = latex_parts.pop(0)
            else:
                latex_part = ''
            while latex_parts:
                part = latex_parts.pop(0)
                if part[0] == '*':
                    latex_part += '_' + part[1:]
                else:
                    latex_part += r'\_' + part

            latex_ls.append(latex_part)

        latex_var = r'\ '.join(latex_ls)

        return latex_var

    @classmethod
    def __unit_to_latex(cls, unit, use_exp):
        """ 
        Converts ICOS-units to latex-strings.

        Parameters
        ----------
        unit : str
            A string having the format of an ICOS-unit.
            - as units: '%', 'Bq m-3', 'hPa', 'm s-1', 'nmol mol-1', 
                         '°', '°C', 'µmol mol-1'
            - es units: '%', 'W m-2', 'cm', 'hPa', 'kPa','kg m-1 s-2', 
                         'm', 'm s-1', 'mm', 'mmol mol-1', '°', '°C', 
                         'µmol m-2 s-1', 'µmol mol-1'
            - os units: 'hPa', 'psu', '°', '°C', 'µatm'

        Returns
        -------
        str 
        """

        if use_exp:
            trans_dict = {'µmol mol-1': r'\mu{mol}\,\,{mol}^{-1}',
                          'mmol mol-1': r'{mmol}\,{mol}^{-1}',
                          'nmol mol-1': r'{nmol}\,{mol}^{-1}',
                          'mm': r'{mm}',
                          'µmol m-2 s-1': r'\mu{mol}\,{m}^{-2}\,{s}^{-1}',
                          'µatm': r'\mu{atm}',
                          '°C': r'{}^{\circ}{C}',
                          '°': r'^{\circ}',
                          'hPa': r'{hPa}',
                          'kPa': r'{kPa}',
                          'psu': r'{psu}',
                          '%': r'\%',
                          'cm': r'{cm}',
                          'm s-1': r'{m}\,{s}^{-1}',
                          'W m-2': r'{W}\,{m}^{-2}',
                          'kg m-1 s-2': r'{kg}\,{m}^{-1}\,{s}^{-2}',
                          'Bq m-3': r'{Bq}\,{m}^{-3}'}
        else:
            trans_dict = {'µmol mol-1': r'\mu{mol}/{mol}',
                          'mmol mol-1': r'{mmol}/{mol}',
                          'nmol mol-1': r'{nmol}/{mol}',
                          'mm': r'{mm}',
                          'µmol m-2 s-1': r'\mu{mol}/{m}^{2}{s}',
                          'µatm': r'\mu{atm}',
                          '°C': r'{}^{\circ}{C}',
                          '°': r'^{\circ}',
                          'hPa': r'{hPa}',
                          'kPa': r'{kPa}',
                          'psu': r'{psu}',
                          '%': r'\%',
                          'cm': r'{cm}',
                          'm s-1': r'{m}/{s}',
                          'W m-2': r'{W}/{m}^{2}',
                          'kg m-1 s-2': r'{kg}/{m}{s}^{2}',
                          'Bq m-3': r'{Bq}/{m}^{3}'}

        if unit in trans_dict.keys():
            latex_unit = trans_dict[unit]
        else:
            latex_unit = unit

        return latex_unit

    # End of class members

    def __init__(self, **configs):
        """
            Use this in order to convert ICOS variables and ICOS units 
            into LaTeX strings to prettify plots etc.
            
            The object has three public methods:
             + var_to_latex(icos_var: str) -> str
             + unit_to_latex(icos_unit: str) -> str
             + var_unit_to_latex(icos_var: str, icos_unit: str) -> str
             
            With configs the user can set stylings of the LaTeX code.
            
            Possible configuration keys:

                - font_style: str.
                    Default is 'rm'. Possible choices are 'rm',
                    'roman', 'sf', 'sans', 'tt', 'it', 'bf',
                    'bb', 'cal', 'frak', 'none',

                - font_size: int or str
                    Default is 8. Possible choices are
                    0, 6, 8, 9, 10, 11, 12, 14, 17, 21, 25
                    0 is a flag to use LaTeX default size, otherwise 
                    it is somewhat similar to font-size points.
                    If `font_size` is not an `int` it will be converted
                    into an `int` or to the default value.

                - use_exp: bool
                    Default is False. If True, output use negative 
                    exponents instead of div-signs (e.g. 'm/s' or 
                    'm s^{-1}').

                - debug: bool
                    Default is False. If True, messages are printed.

                - compiler: str
                    Default value 'mathjax'. At this moment the code is implemented
                    for MathJax engine https://www.mathjax.org/
                    See the warning in (***)
        """

        self._config = {}
        self.__process_configs(**configs)

    def __process_configs(self, **configs):

        layout_keys = list(Translator.__layout.keys())

        debug = configs.pop('debug', False)
        self['debug'] = debug if isinstance(debug, bool) else False
        self['compiler'] = configs.pop('compiler', None)

        # Only set known keys:
        for k in layout_keys:
            if k in configs.keys():
                self[k] = configs.pop(k, None)
            else:
                self[k] = None

        if configs and self.debug:
            known_keys = layout_keys.extend(['debug', 'compiler'])
            unknown_keys = [str(x) for x in configs.keys()]
            msg = f'''\tUnknown key(s) sent to `icos2latex`: \
            \n\t\t{", ".join(unknown_keys)}.\
            \n\tKnown keys are:  \
            \n\t\t{", ".join(known_keys)}.'''
            print(msg)

    def __setitem__(self, key, value):
        if key in ['debug', 'use_exp']:
            if isinstance(value, bool):
                self._config[key] = value
            else:
                self._config[key] = False
        elif key in Translator.__layout.keys():
            self._config[key] = Translator.__layout[key].get(str(value), None)
        elif key == 'font_style':
            self._config[key] = Translator.__layout[key].get(str(value), None)
        elif key == 'compiler':
            if value is None:
                self._config[key] = 'mathjax'
            else:
                self._config[key] = str(value)
        else:
            if self.debug:
                msg = f"""\tError in the call to `icos2latex`: """ \
                      f"""\n\t\tUnknown parameter `{key}`. """ \
                      f"""\n\t{self.__init__.__doc__}"""
                print(msg)

    def __getitem__(self, key):
        return self._config[key]

    def __str__(self, msg=None):
        return self.__init__.__doc__

    @property
    def font_size(self):
        return self['font_size']

    @property
    def font_style(self):
        return self['font_style']

    @property
    def use_exp(self):
        return self['use_exp']

    @property
    def debug(self):
        return self['debug']

    @property
    def compiler(self):
        return self['compiler']

    def __set_style(self, latex_txt, no_dollars: bool = False):
        """ 
        Returns a latex string of latex_txt 
        with size according to the layout
        """

        if self.font_style is not None:
            txt = f'{{{self.font_style} {{{latex_txt}}}}}'
        else:
            txt = latex_txt

        # See the "Warning" paragraph in the file documentation
        if self.font_size is not None:
            if self.compiler == 'mathjax' and not no_dollars:
                # in case the output should be compiled with mathjax
                latex_final = fr'${{{self.font_size} {txt}}}$'
            elif not no_dollars:
                # in case the output should go into an ordinary tex-file
                latex_final = fr'{self.font_size} {{${txt}$}}'
            else:
                latex_final = fr'{self.font_size} {{{txt}}}'
        elif not no_dollars:
            latex_final = f'${txt}$'
        else:
            latex_final = f'{txt}'

        return latex_final

    def var_to_latex(self, var: str = None,
                     no_dollar: bool = False):
        """ 
        Converts ICOS-variables to latex-strings.

        Parameters
        ----------
            var: str
                Expects a string having the format of an ICOS-variable
                (see the formats __var_to_latex())
            no_dollar: bool
                If True the return value is without '$' signs.

        Returns
        -------
        str 

        """

        if not isinstance(var, str):
            return ''

        latex_var = Translator.__var_to_latex(var)

        return self.__set_style(latex_txt=latex_var, no_dollars=no_dollar)

    def unit_to_latex(self, unit: str = None, no_dollar: bool = False):
        """ 
        Converts ICOS-units to latex-strings 
        WITH $-signs, using settings from the layout 

        Parameters
        ----------
            unit: str
                Expects a string having the format of an
                ICOS-unit (see formats in __unit_to_latex()).
            no_dollar: bool
                If True the return value is without '$' signs.

        Returns
        -------
        str 
        """

        if not isinstance(unit, str):
            return ''

        latex_unit = self.__unit_to_latex(unit, self.use_exp)

        return self.__set_style(latex_txt=latex_unit, no_dollars=no_dollar)

    def var_unit_to_latex(self, var_unit: (str, str) = None,
                          var_ls: [str] = None,
                          unit: str = None):
        """
            Converts ICOS-var and ICOS-unit into latex-strings

            Parameters
            ----------
            var_unit: (str, str))
                A tuple in the form (var, unit) where var and
                unit are like below.
            var_ls  : list of strings
                Expects a list of strings where each string has
                the format of an ICOS-variable, it will then return a comma
                separated list of latex-strings.
            unit : str
                Expects a string having the format of an ICOS-unit
                see doc of __unit_to_latex()

            Example:

            >>> var_unit_to_latex(var_ls = ['SWC1', 'SWC2', 'SWC3'],
            >>>                   unit = '%')
            '${SWC_1},\ {SWC_2},\ {SWC_3},\ (\%)$'

            Returns
            -------
            string
        """

        if var_unit:
            latex_var = Translator.__var_to_latex(var_unit[0])
            latex_unit = Translator.__unit_to_latex(var_unit[1], self.use_exp)
        elif isinstance(var_ls, list):
            latex_vars = [Translator.__var_to_latex(v) for v in var_ls]
            latex_var = r',\ '.join(latex_vars)
            if unit:
                latex_unit = Translator.__unit_to_latex(unit, self.use_exp)
            else:
                latex_unit = None
        else:
            return '$ $'

        if latex_unit:
            latex_unit = f'({latex_unit})'
            latex_var_unit = rf'{latex_var}\ {latex_unit}'
        else:
            latex_var_unit = latex_var
        return self.__set_style(latex_var_unit)
