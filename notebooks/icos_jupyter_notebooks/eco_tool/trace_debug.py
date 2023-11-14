#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    A simple debugger/tracer, where the
    developer can set outputs of stack and variables.
    Use output = 'html' for colorful HTML returns.
"""

__credits__ = "ICOS Carbon Portal"
__license__ = "GPL-3.0"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']
__status__ = "rc1"
__date__ = '2023-09-04'

import inspect


class IDebug:
    def __init__(self,
                 output: str = None,
                 call_id: int = None,
                 keep_outputs: bool = None):
        self.output = output if isinstance(output, str) else ''
        self.call_id = call_id if isinstance(call_id, int) else 0
        self.first_call = True

        if bool(keep_outputs):
            self.trace = {self.call_id: '__init__'}
        else:
            self.trace = None

    def debug_value(self, *text_list,
                    external_id: int = None,
                    stack_start: int = None,
                    stack_depth: int = None):

        def set_css(text: str, css_type: str = None):
            if css_type == 'tight_1':
                return f'<p class="tight_1">{text}</p>'
            else:
                return f'<p class="tight_2">{text}</p>'

        if self.first_call:
            top = '<head>' \
                  '    <style>' \
                  '        p.tight_1 {line-height: 1.2; ' \
                  '            margin-left: 10px;' \
                  '            "font-size:9.0pt"}' \
                  '        p.tight_2 { line-height: 1.0;' \
                  '            margin-left: 30px;' \
                  '            "font-size:6.0pt"}' \
                  '    </style>' \
                  '</head>' \
                  '<hr><h4>Traces start</h4><hr>'
            self.first_call = False
        else:
            top = '<hr>'

        self.call_id += 1

        if isinstance(external_id, int):
            ex_call_id = external_id
        else:
            ex_call_id = self.call_id

        if isinstance(stack_start, int):
            start = stack_start
        else:
            start = 1
        if isinstance(stack_depth, int):
            stop = max(stack_start, stack_depth)
        else:
            stop = start + 1

        caller_stack = []
        for x in range(start, min(stop, len(inspect.stack()))):
            caller_stack.append(f'{inspect.stack()[x][3]}()')

        deb_ls = [f'#call_nr = {self.call_id}',
                  f'#caller(s): {", ".join(caller_stack)}']

        text_list = [str(t) for t in text_list]
        if self.output.lower() != 'html':
            deb_ls.extend(text_list)
            msg = ''.join(deb_ls)
        else:
            # formatting html
            if not text_list:
                text_list = deb_ls.extend([99, '-- start --'])
            color_num = external_id

            r_col = (41 * color_num) % 200
            g_col = (101 * color_num) % 177
            b_col = (137 * color_num) % 151
            header_span = f'<span style="color:rgb({r_col}, ' \
                          f'{g_col}, {b_col})" >'
            row_span = f'<span style="color:rgb({r_col}, ' \
                       f'{g_col}, {b_col})">'
            header_txt = f'<b>{deb_ls[0]} - {deb_ls[1]}</b>'
            debug_line = f'<b>{deb_ls[0]}</b>'
            msg = top
            msg += set_css(f'{header_span}{header_txt}</span>', 'tight_1')
            msg += f'{row_span}'
            row_label = f'<br> -- {debug_line} --- '
            msg_rows = ''
            for text in text_list:
                msg_rows += row_label + text

            msg_rows += '</span>'

            msg += set_css(msg_rows, 'tight_2')
        if self.trace:
            self.trace[self.call_id] = msg
        return msg
