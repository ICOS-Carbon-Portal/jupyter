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
        if bool(keep_outputs):
            self.trace = {self.call_id: '__init__'}
        else:
            self.trace = None

    def debug_value(self, *text_list,
                    external_id: int = None,
                    stack_start: int = None,
                    stack_depth: int = None):
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
            margin = '&nbsp' * 6  # html space
            color_num = external_id

            r_col = (41 * color_num) % 200
            g_col = (101 * color_num) % 177
            b_col = (137 * color_num) % 151
            header_span = f'<span style="color:rgb({r_col}, ' \
                          f'{g_col}, {b_col})"; "font-size:10.0pt">'
            row_span = f'<span style="color:rgb({r_col}, ' \
                       f'{g_col}, {b_col})"; "font-size:8.0pt">'
            header_txt = f'<b>{deb_ls[0]} - {deb_ls[1]}</b>'
            debug_line = f'<b>{deb_ls[0]} </b>'
            msg = f'{header_span}{margin} {header_txt} {margin}</span>'
            msg += f'{row_span}'
            row_label = f'<br>{margin} -- {debug_line} {margin} -- '
            msg += f'{row_label}'.join(text_list)
            msg += '</span>'
        if self.trace:
            self.trace[self.call_id] = msg
        return msg
