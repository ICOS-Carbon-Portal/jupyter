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
import time


class IDebug:
    def __init__(self,
                 output: str = None,
                 auto_refresh: bool = None,
                 hide_output: bool = None,
                 stack_start: int = None,
                 stack_stop: int = None):
        self.output = output if isinstance(output, str) else ''
        self.call_id = 0
        self.output_id = 0
        if isinstance(stack_start, int) and stack_start >= 0:
            self.stack_start = stack_start
        else:
            self.stack_start = 2
        if isinstance(stack_stop, int) and stack_stop > self.stack_start:
            self.stack_stop = stack_stop
        else:
            self.stack_stop = max(5, self.stack_start + 1)

        self.auto_refresh = bool(auto_refresh)
        self.hide_output = bool(hide_output)
        self.first_call = True
        self.trace = {self.call_id:
                          dict(timer_id=0,
                               time=time.time(),
                               text_header='<head>'
                                           '    <style>'
                                           '        p.tight_header '
                                           '            {line-height: 1.2;'
                                           '             margin-left: 10px;'
                                           '             font-size: 9.0pt}'
                                           '        p.tight_header_long_margin '
                                           '            {line-height: 1.2;'
                                           '             margin-left: 20px;'
                                           '             font-size: 9.0pt}'
                                           '        p.tight_timer '
                                           '            {color: red; '
                                           '             line-height: 1.0;'
                                           '             margin-left: 20px;'
                                           '             font-size: 7.0pt}'
                                           '        p.tight_body '
                                           '            {line-height: 1.0;'
                                           '             margin-left: 30px;'
                                           '             font-size: 6.0pt}'
                                           '        p.tight_body_long_margin '
                                           '            {line-height: 1.0;'
                                           '             margin-left: 60px;'
                                           '             font-size: 6.0pt}'
                                           '    </style>'
                                           '</head>'
                                           '<hr>',
                               text_body='')
                      }

    def fetch_traces(self):
        def set_css(txt: str, css_type: str, use_long_margin: bool):
            margin = '_long_margin' if use_long_margin else ''
            if css_type == 'header':
                return f'<p class="tight_header{margin}">{txt}</p>'
            elif css_type == 'timer':
                return f'<p class="tight_timer">{txt}</p>'
            else:
                return f'<p class="tight_body{margin}">{txt}</p>'

        time_0 = self.trace[0]['time']
        if self.output != 'html':
            txt_top = ''
        else:
            txt_top = str(self.trace[0]['text_header'])

        keys = [k for k in self.trace.keys() if k >= self.output_id]
        if not keys:
            return
        self.output_id = max(keys) + 1
        timer_dict = {}
        msg = txt_top
        for k in keys:
            long_margin = False
            time_k = self.trace[k]['time']
            timer_id = self.trace[k]['timer_id']

            if timer_id in timer_dict.keys():
                time_deltas = [str(time_k - t) for t in timer_dict[timer_id]]
                timer_dict[timer_id].append(time_k)
                time_deltas.append(str(time_k - time_0))
                long_margin = True
            else:
                timer_dict[timer_id] = [time_k]
                time_deltas = [str(time_k - time_0)]

            if self.output.lower() != 'html':
                time_delta = f'\n\tTotal runtime: {time_deltas[-1]}'
                if len(time_deltas) > 1:
                    time_delta = f'\n\tTime deltas: ' \
                                 f'{", ".join(time_deltas[:-1])}' \
                                 f'{time_delta}'
                time_txt = f'{time_delta}\n\tTimer id: {timer_id}\n'
                msg += f"{self.trace[k]['text_body']} \n\t {time_txt}"
            else:
                len_time_deltas = len(time_deltas)

                time_delta_k = f'<br>Total runtime: {time_deltas[-1]}'
                time_delta = ''
                if len_time_deltas > 1:
                    time_delta = f'Time deltas: ' + ', '.join(time_deltas[:-1])
                time_delta += time_delta_k
                time_txt = f'{time_delta}<br>Timer id: {timer_id}'

                msg += set_css(txt=self.trace[k]['text_header'],
                               css_type='header', use_long_margin=long_margin)
                msg += set_css(txt=time_txt,
                               css_type='timer', use_long_margin=long_margin)
                msg += set_css(txt=self.trace[k]['text_body'],
                               css_type='body', use_long_margin=long_margin)
        return msg

    def reset_trace(self, block: int = None):
        if not isinstance(block, int):
            self.trace = {0: self.trace[0]}
        else:
            keys = [0] + list(self.trace.keys())[block:]
            self.trace = {k: v for k, v in self.trace.items() if k in keys}

    def debug_value(self, *text_list,
                    timer_id: int = None):

        self.call_id += 1

        timer_id = timer_id if isinstance(timer_id, int) else 1
        temp_trace = {'timer_id': timer_id,
                      'time': time.time()}

        caller_stack = []
        for x in range(self.stack_start, min(self.stack_stop,
                                             len(inspect.stack()))):
            caller_stack.append(f'{inspect.stack()[x][3]}()')

        deb_ls = [f'#call_nr = {self.call_id}',
                  f'#caller(s): {", ".join(caller_stack)}']

        text_list = [str(t) for t in text_list]
        if self.output.lower() != 'html':
            deb_ls.extend(text_list)
            temp_trace['text_body'] = '\n'.join(deb_ls)
        else:
            # formatting html
            if not text_list:
                text_list = deb_ls.extend([99, '-- start --'])
            color_num = timer_id
            r_col = (41 * color_num) % 200
            g_col = (101 * color_num) % 177
            b_col = (137 * color_num) % 151
            color_style = f'style="color:rgb({r_col}, {g_col}, {b_col})"'
            header_txt = f'<b>{deb_ls[0]} - {deb_ls[1]}</b>'
            debug_line = f'<b>{deb_ls[0]}</b>'
            text_header = f'<hr><span {color_style}>{header_txt}</span>'
            temp_trace['text_header'] = text_header

            row_label = f'<br> -- {debug_line} --- '
            msg_rows = ''
            for text in text_list:
                msg_rows += row_label + text
            text_body = f'<span {color_style}>{msg_rows}</span>'
            temp_trace['text_body'] = text_body
            self.trace[self.call_id] = temp_trace
        if self.auto_refresh:
            return self.fetch_traces()
