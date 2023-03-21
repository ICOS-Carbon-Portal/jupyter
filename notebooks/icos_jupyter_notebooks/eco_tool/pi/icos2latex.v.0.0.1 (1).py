#!/usr/bin/env python
# -*- coding: utf-8 -*-
#01234567890123456789012345678901234567890123456789012345678901234567890
"""
    Convert ICOS variables and ICOS units into LaTeX-snippets. 
    
    Examples
    --------
    >>> latex.var_to_latex('CO2')
    '${\\scriptsize {\\mathrm {CO_2}}}$'

    >>> latex.unit_to_latex('µmol mol-1', size=10, font_style = 'sans')
    '${\\small {\\mathsf {\\mu{mol}/{mol}}}}$'
    
    >>> latex.var_unit_to_latex('CO2''µmol mol-1', size=14, font_style = 'bf')
    '${\\Large {\\mathbf {CO_2}}}\\ {\\Large ({\\Large {\\mathbf {\\mu{mol}/{mol}}}})}$'
    
    Warning
    -------
    Regarding the size commands, they should not be used in math
    mode. Compiling (outside python) ${\small {x}}$ yields a LaTeX-
    warning. A correct LaTeX-string would be \small{$x$}. 
    However, at least for plotly, expects all LaTeX-code to be within $-signs. 
    Also, plotly use mathjax, other packages might have other solutions. 
    If by some reason code compilation fails, try to set size = 0 in your call.
    
"""

__author__      = ["Anders Dahlner"]
__credits__     = "ICOS Carbon Portal"
__license__     = "GPLv3+"
__version__     = "0.1.0"
__maintainer__  = "ICOS Carbon Portal, Elaborated products team"
__email__       = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']


_settings = {'size': 
             {6: r'\tiny ',         # ~6pt
              7: r'\scriptsize ',   # Note: ~8pt
              8: r'\scriptsize ',   # ~8pt
              9: r'\footnotesize ', # ~9pt
              10: r'\small ',       # ~10pt, *default
              11: r'\normalsize ',  # ~11pt
              12: r'\large ',       # etc...
              14: r'\Large ',
              17: r'\LARGE ',
              21: r'\huge ',
              25: r'\Huge ', 
              0: ''},                # See (***) above 
             'font_style':
             {'rm': r'\mathrm ',     # serif, ~times roman, *default 
              'roman': r'\mathrm ',  # ---
              'sf': r'\mathsf ',     # sans-serif, no serifs, web-text
              'sans': r'\mathsf ',   # ---
              'tt': r'\mathtt ',     # serif, typewriter text
              'it': r'\mathit ',     # serif, italic, ~ like default latex
              'bf': r'\mathbf ',     # serif, bold
              'bb': r'\mathbb ',     # black-board bold, for capitals
              'cal': r'\mathcal ',   # calligraphy, for capitals 
              'frak': r'\mathfrak ', # fraktur, for capitals
              'none': ''},           # default latex style 
             'use_exp': False        # Applies to units, if use_exp == True 
            }                        # then use negative exponents instead of div-sign


def _set_dollars(latex_txt, **layout):
    """ 
    Returns a latex string of latex_txt 
    with size according to the layout
    """
    
    size_cmd = _get_size_cmd(**layout)

    # See the "Warning" paragraph in the file comments
    latex_txt = fr'${{{size_cmd}{latex_txt}}}$'
    return latex_txt


def _get_size_cmd(**layout):
    """ 
    Returns the size command according to the layout
    """
    
    if 'size' in layout.keys() and \
    layout['size'] in _settings['size'].keys():
        size_cmd = _settings['size'][layout['size']]
    else:
        size_cmd = _settings['size'][8]
    return size_cmd


def _get_style_cmd(**layout):
    """
    Returns font-style command to be used in math mode
    """
    if 'font_style' in layout.keys() and \
    layout['font_style'] in _settings['font_style'].keys():  
        font_cmd = _settings['font_style'][layout['font_style']]
    else:
        font_cmd = _settings['font_style']['rm']
    return font_cmd


def var_to_latex(var,**layout):
    """ 
    Converts ICOS-variables to latex-strings.
    
    Parameters
    ----------
    var : str
        Expects a string having the format of an ICOS-variable
        (see the formats below)
        
    Returns
    -------
    str 
    """
      # var,unit:  
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
    
    trans_dict = {'CO2'    : r'{{CO_2}}',
                  'co2'    : r'{{CO_2}}',
                  'fCO2'   : r'{{fCO_2}}',
                  'pCO2'   : r'{{pCO_2}}',
                  'co'     : r'{{CO}}',
                  'ch4'    : r'{{CH_4}}',
                  'H2O'    : r'{{H_2O}}',
                  'n2o'    : r'{{N_2O}}',
                  'rn'     : r'{{RN}}',
                  '[degC]' : r'{{[^{\circ}C]}}',
                  '[uatm]' : r'{{[\mu {atm}]}}'}
    cmd = _get_style_cmd(**layout)
    
    var_ls = var.split(' ')
    latex_ls = []
    var_word_ls = []

    for word in var_ls:
        word_parts = word.split('_')
        latex_parts = []
        while word_parts:
            word_part = word_parts.pop(0)
            if word_part in trans_dict.keys():
                tex_txt = trans_dict[word_part]
            elif word_part.isdigit():
                digit_ls = [word_part]
                while word_parts and word_parts[0].isdigit():
                    digit_ls.append(word_parts.pop(0))
                if len(digit_ls)==1:
                    tex_txt = '*' + digit_ls[0]
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
    latex_var = f'{{{cmd}{{{latex_var}}}}}'

    return _set_dollars(latex_var,**layout)


def unit_to_latex(unit,**layout):
    """ 
    Converts ICOS-units to latex-strings.
    
    Parameters
    ----------
    unit : str
        Expects a string having the format of an ICOS-unit
        (see the formats below)
        
    Returns
    -------
    str 
    """

    # as units : {'%', 'Bq m-3', 'hPa', 'm s-1', 'nmol mol-1', '°', '°C', 'µmol mol-1'}
    # es units : {'%', 'W m-2', 'cm', 'hPa', 'kPa','kg m-1 s-2', 'm', 'm s-1', 'mm', 'mmol mol-1', '°', '°C', 'µmol m-2 s-1', 'µmol mol-1'}
    # os units : {'hPa', 'psu', '°', '°C', 'µatm'}
    
    if 'use_exp' in layout.keys():
        use_exp = layout['use_exp']
    else:
        use_exp = _settings['use_exp']
    
    if use_exp:
        trans_dict = {'µmol mol-1'  : r'\mu{mol}\,\,{mol}^{-1}',
                      'mmol mol-1'  : r'{mmol}\,{mol}^{-1}',
                      'nmol mol-1'  : r'{nmol}\,{mol}^{-1}',
                      'mm'          : r'{mm}',
                      'µmol m-2 s-1': r'\mu{mol}\,{m}^{-2}\,{s}^{-1}', 
                      'µatm'        : r'\mu{atm}', 
                      '°C'          : r'{}^{\circ}{C}', 
                      '°'           : r'^{\circ}', 
                      'hPa'         : r'{hPa}',
                      'kPa'         : r'{kPa}',
                      'psu'         : r'{psu}',
                      '%'           : r'\%',
                      'cm'          : r'{cm}',
                      'm s-1'       : r'{m}\,{s}^{-1}',
                      'W m-2'       : r'{W}\,{m}^{-2}',
                      'kg m-1 s-2'  : r'{kg}\,{m}^{-1}\,{s}^{-2}',
                      'Bq m-3'      : r'{Bq}\,{m}^{-3}'}
    else: 
        trans_dict = {'µmol mol-1'  : r'\mu{mol}/{mol}',
                      'mmol mol-1'  : r'{mmol}/{mol}',
                      'nmol mol-1'  : r'{nmol}/{mol}',
                      'mm'          : r'{mm}',
                      'µmol m-2 s-1': r'\mu{mol}/{m}^{2}{s}', 
                      'µatm'        : r'\mu{atm}', 
                      '°C'          : r'{}^{\circ}{C}', 
                      '°'           : r'^{\circ}', 
                      'hPa'         : r'{hPa}',
                      'kPa'         : r'{kPa}',
                      'psu'         : r'{psu}',
                      '%'           : r'\%',
                      'cm'          : r'{cm}',
                      'm s-1'       : r'{m}/{s}',
                      'W m-2'       : r'{W}/{m}^{2}',
                      'kg m-1 s-2'  : r'{kg}/{m}{s}^{2}',
                      'Bq m-3'      : r'{Bq}/{m}^{3}'}
        
    if unit in trans_dict.keys(): 
        latex_unit = trans_dict[unit]
    else:
        latex_unit = unit
    
    cmd = _get_style_cmd(**layout)
    latex_unit = fr'{{{cmd}{{{latex_unit}}}}}'
    
    return _set_dollars(latex_unit,**layout)


def var_unit_to_latex(var,unit,**layout):
    """ 
    Converts ICOS-vars and ICOS-units into latex-strings.
    
    Parameters
    ----------
    var  : str
        Expects a string having the format of an ICOS-variable
    
    unit : str
        Expects a string having the format of an ICOS-unit
        
    Returns
    -------
    str 
    """
    
    latex_var = var_to_latex(var,**layout)
    latex_unit = unit_to_latex(unit,**layout)
    try:
        latex_var = latex_var[1:-1]
        latex_unit = latex_unit[1:-1]
        latex_unit = f'({latex_unit})'
        latex_unit = _set_dollars(latex_unit,**layout)[1:-1]
    except:
        pass
    
    latex_var_unit = f'${latex_var}\ {latex_unit}$'
        
    return latex_var_unit
    
    
    
