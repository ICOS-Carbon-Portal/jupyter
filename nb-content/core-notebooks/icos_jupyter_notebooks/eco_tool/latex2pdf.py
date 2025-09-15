#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Use the class LaTeX to compile tex-files
    or LaTeX-code into a pdf.

    Static functions
    ----------------
    create_pdf()
    create_tex_file()

    Member functions
    ----------------
    code_to_pdf()
    file_to_pdf()

"""

__credits__ = "ICOS Carbon Portal"
__license__ = "GPL-3.0"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']
__status__ = "rc1"
__date__ = "2023-09-01"

import os
import subprocess
import eco_tool.os_funcs as os2


class LaTeX:
    compile_types = ['bib', 'label', 'default']
    default_settings = {'_output_folder': 'pdf_files',
                        '_tex_folder': 'tex_files',
                        '_preamble': '\n'.join([r'% This is a LaTeX-template. ',
                                                '',
                                                r'\documentclass[12pt,a4paper]'
                                                r'{article}',
                                                r'\usepackage[utf8]{inputenc}',
                                                r'\usepackage{amsmath}',
                                                r'\usepackage{amsfonts}',
                                                r'\usepackage{amssymb}',
                                                r'\usepackage{graphicx}',
                                                r'\graphicspath{ {./images/} }',
                                                r'\usepackage{hyperref}',
                                                '',
                                                r'% --- end of LaTeX '
                                                r'preamble ---'])}

    @staticmethod
    def create_pdf(tex_file_path: str,
                   output_folder: str = None,
                   compile_type: str = None,
                   remove_garbage: bool = None,
                   no_compile_exception: bool = None,
                   debug: bool = None) -> str:

        r"""
            Compiles latex file into pdf.

            Inputs
            ------

            - tex_file_path: str
                    Path to the file.

            - output_folder: str
                    Default = LaTeX.default_settings['_output_folder']
                    Path to output folder.

            - compile_type: str
                    Default = 'default'
                    Use the case:
                        'label'     when the tex-file include hyperref
                                    commands like \label, \url \ref, etc.
                                    which requires 2 pdflatex runs.
                        'bib'       when the tex-file include a bib-file in
                                    order to generate a bibliography,
                                    for example:
                                    \bibliography{./tex/my_references.bib}
                                    This requires 3 pdflatex runs and 1
                                    bibtex run.
                        'default'   in order to execute just one pdflatex.
                    Will raise an OS-Error in case the tex-code leads to a
                    compilation error, unless no_compile_exception = True

            - remove_garbage:bool
                    Default = True
                    When True and the pdf-compilation is successful all
                    compilation related files except for the pdf-file
                    will be removed.

            - no_compile_exception: bool
                    Default = False
                    If True, compilation errors will not lead to raised
                    exception but errors we be saved to file in the
                    output-folder.

            - debug: bool
                    Default = False
                    When True error messages will be printed.

            Output
            ------
            - relative path to created pdf
        """
        debug = True if bool(debug) is True else False
        if not isinstance(remove_garbage, bool):
            remove_garbage = True
        if not isinstance(no_compile_exception, bool):
            no_compile_exception = False

        if debug:
            print('LaTeX.create_pdf inputs: ',
                  f'\n\ttex_file_path = {tex_file_path}',
                  f'\n\toutput_folder = {output_folder}',
                  f'\n\tcompile_type = {compile_type}',
                  f'\n\tremove_garbage  = {remove_garbage}')

        if isinstance(compile_type, str) and \
                compile_type.lower() in LaTeX.compile_types:
            compile_type = compile_type.lower()
        else:
            compile_type = 'default'

        if not isinstance(tex_file_path, str):
            raise AttributeError(f'Expected: a path like string tex_file, '
                                 f'received:  {type(tex_file_path)}.')
        if not os.path.isfile(tex_file_path):
            raise FileNotFoundError(
                f'Could not find the file `{tex_file_path}`.')

        if not isinstance(output_folder, str):
            output_folder = LaTeX.default_settings['_output_folder']

        if not os.path.isdir(output_folder):
            temp_output = os2.makedirs_mod(output_folder)
            if not os.path.isdir(temp_output):
                err_msg = f'Could not find the directory `{output_folder}`'
                if temp_output != output_folder:
                    err_msg += f' (or the modified directory `{temp_output}`)'
                raise OSError(err_msg + '.')
            else:
                output_folder = temp_output

        path_to_tex, tex_file_name = os.path.split(tex_file_path)
        file_name, _ = os.path.splitext(tex_file_name)

        aux_file = os.path.join(output_folder, file_name + '.aux')
        log_file = os.path.join(output_folder, file_name + '.log')
        pdf_file = os.path.join(output_folder, file_name + '.pdf')

        if debug:
            print(f'LaTeX.create_pdf paths.',
                  f'\n\tpath to tex folder: path_to_tex = {path_to_tex}',
                  f'\n\tcontent of TeX folder: {os.listdir(path_to_tex)}',
                  f'\n\ttex_file_name = {tex_file_name}',
                  f'\n\toutput_folder = {output_folder}',
                  f'\n\tabs path to output: {os.path.abspath(output_folder)}'
                  f'\n\tcontent of output dir: {os.listdir(output_folder)}')

        # compile commands
        pdf_latex_standard = ['pdflatex', tex_file_path,
                              f'-output-directory={output_folder}',
                              '-interaction=nonstopmode']
        pdf_latex_draft = pdf_latex_standard + ['-draftmode']
        bibtex = ['bibtex', aux_file]

        if compile_type == 'default':
            cmds = [pdf_latex_standard]
        elif compile_type == 'label':
            cmds = [pdf_latex_draft,
                    pdf_latex_standard]
        else:
            # compile_type == 'bib'
            cmds = [pdf_latex_draft,
                    bibtex,
                    pdf_latex_draft,
                    pdf_latex_standard]

        # List to collect compile errors of the os-calls
        error_ls = []
        for cmd in cmds:
            completed_proc = subprocess.run(cmd, stdout=subprocess.PIPE)
            if completed_proc.returncode != 0:
                byte_str = completed_proc.stdout
                byte_str = byte_str.replace(b'\r\n', b'\n\t\t')
                byte_str = byte_str.decode("utf-8")
                error_ls.append(f'\nCommand: {completed_proc.args}. '
                                f'\nReturncode: {completed_proc.returncode}. '
                                f'\nOutput: \n\t\t{byte_str}')
        if error_ls:
            error_file_path = os.path.join(output_folder,
                                           file_name + '_error.log')
            error_msg = f'Problem in the pdflatex compilation of ' + \
                        f'\n\t-- The file: {tex_file_path} ' + \
                        f'\n\t-- Using the destination folder: ' + \
                        f'{output_folder}' + \
                        f'\n\t-- Path to error file: {error_file_path}'

            if os.path.isfile(pdf_file):
                error_msg += f'\n\n\t* Make sure that the file {pdf_file} ' \
                             f'is not open (perhaps by some other ' \
                             f'application)' + \
                             f'\n\t  which might lock the file in ' + \
                             f'"read-only" mode.'
            if os.path.isfile(log_file):
                error_msg += f'\n\n\t* Detailed compilation errors ' \
                             f'might be found in the log-file: {log_file}.'
            with open(error_file_path, 'w') as f:
                f.write(error_msg)

            if os.path.isfile(error_file_path):
                error_append_msg = f'\n\n\t* Shorter compilation details ' \
                                   f'might be found in the error-log-file: ' \
                                   f'{error_file_path}.'
                with open(error_file_path, 'a') as f:
                    f.write(error_append_msg)
                error_msg += error_append_msg

            error_msg += f'\n\n'
            for i in range(len(error_ls)):
                e = error_ls[i]
                error_append_msg = f'\n\n\t***Error {1 + i} (out of ' \
                                   f'{len(error_ls)} errors)***\n{e}'
                with open(error_file_path, 'a') as f:
                    f.write(error_append_msg)
                error_msg += error_append_msg
                # error_append_bytes_msg = e[1].decode("utf-8")
                # with open(error_file_path, 'ab') as f:
                #     f.write(error_append_bytes_msg)
                # error_msg += str(error_append_bytes_msg)

            if debug:
                print(f'LaTeX.create_pdf error_file is stored here:'
                      f' {error_file_path}')
            if not no_compile_exception:
                raise OSError(error_msg)
        elif remove_garbage:
            for f in os.listdir(output_folder):
                f_name, f_ext = os.path.splitext(f)
                if f_name in [file_name, file_name + '.synctex'] and \
                        f_ext in ['.aux', '.log', '.out', '.blg', '.bbl', '.gz']:
                    path_to_f = os.path.join(output_folder, f)
                    if os.path.isfile(path_to_f):
                        os.remove(path_to_f)
        return os.path.relpath(pdf_file)

    @staticmethod
    def _prepare_tex_file_path(tex_file_path: str = None,
                               tex_dir: str = None,
                               debug: bool = None) -> str:
        """
            Modifies suggested tex_file_path with a unique
            filename using a date timestamp and a counter.
            The function will also create parent dictionaries
            of the file.
            No write validation is used and the function
            might raise OSError, PermissionError or FileNotFoundError
            depending on os-access and validation of the suggested name.

            Inputs
            ------
                - tex_file_path: str
                        Default = 'tex-file.tex'
                        Suggested path to tex-file.

                - tex_dir: str
                        Default = LaTeX.default_settings['_tex_folder']
                        Only used if no path is given in tex_file_path
                        Default value 'tex_files'

            Output:
            -------
                - relpath to tex-file to be created
        """

        debug = debug if bool(debug) is True else False
        if debug:
            print(f'_prepare_tex_file_path inputs'
                  f'\n\t -- tex_file_path = {tex_file_path}'
                  f'\n\t -- tex_dir = {tex_dir}')

        if not isinstance(tex_dir, str):
            tex_dir = LaTeX.default_settings['_tex_folder']
        elif tex_dir == '':
            tex_dir = '.'

        if not isinstance(tex_file_path, str):
            pre_path = os.path.join(tex_dir, 'tex-file.tex')
        elif os.path.isdir(tex_file_path):
            pre_path = os.path.join(tex_file_path, 'tex-file.tex')
        else:
            path, file = os.path.split(tex_file_path)
            if path == '':
                path = tex_dir
            if not os.path.isdir(path):
                path = os2.makedirs_mod(path)
            name, ext = os.path.splitext(file)
            if not name:
                file = 'tex-file.tex'
            elif ext != '.tex':
                file = name + '.tex'
            pre_path = os.path.join(path, file)

        rel_path = os2.get_unique_filename(pre_path,
                                           date_stamp=True,
                                           debug=debug)
        if debug:
            print(f'_prepare_tex_file_path '
                  f'\n\t-- tex_file_path = {tex_file_path}'
                  f'\n\t-- pre_path = {pre_path}'
                  f'\n\t-- return_path = {rel_path}')

        return rel_path

    @staticmethod
    def create_tex_file(tex_code: str = None,
                        full_code: bool = None,
                        tex_file_path: str = None,
                        tex_dir: str = None,
                        preamble: str = None,
                        debug: bool = None) -> str:
        r"""
            Uses a tex-template, unless the parameter preamble
            is given, to create a tex-file.

            Inputs:
            -------
            - tex_code: str
                    Default = ' '
                    In the case full_code is
                     False:
                        then tex_code will be handled as the
                        document-part of a tex-file, i.e. like in
                        ...
                        \begin{document}
                            tex_code
                        \end{document}
                        otherwise an example tex-file and pdf is created.
                    True:
                        and tex_code is a non-empty string, then tex_code
                        will be handled as the full latex otherwise an
                        example tex-file and pdf is created.

            - full_code: bool
                    Default: False
                    if True then tex_code is expected to be the full
                    content of the tex-file, see above comment.

            - tex_file_path: str
                    Default = 'tex-file.tex'
                    path to the file to be created.
                    parent directories will be created if necessary.
                    if the file name exists it will be extended with
                    a counter.

            - tex_dir: str
                    Default = LaTeX.default_settings['_tex_folder']
                    Only used if no path is given in tex_file_path

            - preamble: str
                    Valid only if full_code is False:
                    Default = LaTeX.default_settings['_preamble']
                    The preamble-part of the tex-file,
                    i.e. like this
                        preamble  % this is the preamble part of a tex-file
                        \begin{document}
                        ...

            Output:
            ------
            - relative path to created tex-file
        """

        debug = debug if isinstance(debug, bool) else False
        full_code = full_code if isinstance(full_code,bool) else False
        if debug:
            print('LaTeX.create_tex_file inputs: ',
                  f'\n\ttex_file_path = {tex_file_path}')

        if not tex_code:
            tex_code = ' '
        elif not isinstance(tex_code, str):
            raise AttributeError(f'Expected: a string tex_code, received:  '
                                 f'{type(tex_code)}.')

        file_relpath = LaTeX._prepare_tex_file_path(tex_file_path=tex_file_path,
                                                    tex_dir=tex_dir,
                                                    debug=debug)
        if full_code:
            file_content = tex_code
        else:
            if not isinstance(preamble, str):
                preamble = LaTeX.default_settings['_preamble']

            file_content = '\n'.join([preamble,
                                      r'\begin{document}',
                                      tex_code,
                                      r'\end{document}'])
        try:
            with open(file_relpath, "w") as f:
                f.write(file_content)
        except Exception:
            raise OSError(f'Could not create the file {file_relpath}')

        if not os.path.isfile(file_relpath):
            raise OSError(f'Could not create the file: {file_relpath}.')
        return file_relpath

    def __init__(self,
                 tex_folder: str = None,
                 output_folder: str = None,
                 compile_type: str = None,
                 remove_garbage: str = None,
                 debug: bool = None):
        r"""
            LaTeX settings.

            Inputs
            ------
            - tex_folder: str = None
                    path to tex-files. If None the folder './tex_files'
                    will be used. The folder will be created if needed.

            - output_folder: str = None
                    path to pdf-files (and other LaTeX produced files).
                    If None the folder './pdf_files' will be used.
                    The folder will be created if needed.

             - compile_type: str
                    Default = 'default'
                    Use the case:
                        'label'     when the tex-file include hyperref
                                    commands like \label, \url \ref, etc.
                                    which requires 2 pdflatex runs.
                        'bib'       when the tex-file include a bib-file in
                                    order to generate a bibliography,
                                    for example:
                                    \bibliography{./tex/my_references.bib}
                                    This requires 3 pdflatex runs and 1
                                    bibtex run.
                        'default'   in order to execute just one pdflatex.

             remove_garbage: bool
                    Default = True
                    When True and the pdf-compilation is successful all
                    compilation related files except for the pdf-file
                    will be removed.

           - debug: bool
                    Default = False
                    When True error messages will be printed.

            Output
            ------
            - relative path to created pdf
        """

        if isinstance(tex_folder, str):
            self.tex_folder = tex_folder
        else:
            self.tex_folder = LaTeX.default_settings['_tex_folder']

        if isinstance(output_folder, str):
            self.output_folder = output_folder
        else:
            self.output_folder = LaTeX.default_settings['_output_folder']

        if isinstance(compile_type, str) and \
                compile_type.lower() in LaTeX.compile_types:
            self.compile_type = compile_type.lower()
        else:
            self.compile_type = 'default'

        if not isinstance(remove_garbage, bool):
            self.remove_garbage = True
        else:
            self.remove_garbage = remove_garbage

        self.debug = True if bool(debug) is True else False

    def file_to_pdf(self,
                    tex_file_path: str,
                    compile_type: str = None) -> str:
        """
            Compile a specific LaTeX-file into a pdf.

            Inputs:
            -------
            - tex_file_path: str
                    file name, or local path to latex-file.

            - compile_type: str
                    overrides self.compile_type

            Output:
            -------
            - relative path to pdf-file

        """

        if not isinstance(tex_file_path, str):
            raise TypeError(f'Expected: the parameter `tex_file_path` '
                            f'should be a string. '
                            f'Received:  {type(tex_file_path)}.')
        elif not os.path.exists(tex_file_path):
            path_to_file = os.path.join(self.tex_folder, tex_file_path)
            if not os.path.exists(path_to_file):
                err_msg = f'Could not find {tex_file_path}'
                if tex_file_path != path_to_file:
                    err_msg += f' or {path_to_file}'
                raise FileNotFoundError(err_msg)
        else:
            path_to_file = tex_file_path

        if isinstance(compile_type, str) and \
                compile_type.lower() in LaTeX.compile_types:
            compile_type = compile_type.lower()
        else:
            compile_type = self.compile_type

        return LaTeX.create_pdf(tex_file_path=path_to_file,
                                output_folder=self.output_folder,
                                compile_type=compile_type,
                                remove_garbage=self.remove_garbage,
                                debug=self.debug)

    def code_to_pdf(self,
                    tex_code: str = None,
                    full_code: bool = None,
                    tex_file_path: str = None,
                    compile_type: str = None) -> str:
        r"""
            Uses a tex-template to create a tex-file and compile
            it into a pdf.

            Inputs:
            -------
            - tex_code: str
                    Default = ' '
                    In the case full_code is
                     False:
                        then tex_code will be handled as the
                        document-part of a tex-file, i.e. like in
                        ...
                        \begin{document}
                            tex_code
                        \end{document}
                        otherwise an example tex-file and pdf is created.
                    True:
                        and tex_code is a non-empty string, then tex_code
                        will be handled as the full latex otherwise an
                        example tex-file and pdf is created.

            - full_code: bool
                    Default: False
                    if True then tex_code is expected to be the full
                    content of the tex-file, see above comment.

            - tex_file_path: str
                    Suggested file name, or local path to latex-file.
                    If no name is provided
                    "self.tex_folder/tex-file_<date_timestamp>.tex"
                    will be used.

            - compile_type: str
                    overrides self.compile_type

            Output:
            -------
            - relative path to pdf-file

        """

        if not isinstance(tex_code, str):
            tex_code = ' '

        if isinstance(compile_type, str) and \
                compile_type.lower() in LaTeX.compile_types:
            compile_type = compile_type.lower()
        else:
            compile_type = self.compile_type

        file_path = LaTeX.create_tex_file(tex_code=tex_code,
                                          full_code=full_code,
                                          tex_file_path=tex_file_path,
                                          tex_dir=self.tex_folder,
                                          debug=self.debug)
        if self.debug:
            print(f'code_to_pdf '
                  f'\n\t-- tex_file_path = {tex_file_path}'
                  f'\n\t-- file_path ={file_path}')

        return LaTeX.create_pdf(tex_file_path=file_path,
                                output_folder=self.output_folder,
                                compile_type=compile_type,
                                remove_garbage=self.remove_garbage,
                                debug=self.debug)
