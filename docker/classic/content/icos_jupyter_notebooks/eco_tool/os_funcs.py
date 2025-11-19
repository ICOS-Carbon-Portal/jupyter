#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    A collection of os functions.
    Functions
    ---------
    get_unique_filename() -> str:
            returns a unique filename.
            Might raise OSError, PermissionError or FileNotFoundError
            depending on os-access and validation of the suggested name.

    makedirs_mod() -> str:
            creates directories of a path,
            similar to os.makedirs but will create
            unique names if a directory of the path
            exists and is not a directory.
            Might raise OSError, PermissionError or FileNotFoundError
            depending on os-access and validation of the suggested name.
"""

__credits__ = "ICOS Carbon Portal"
__license__ = "GPL-3.0"
__version__ = "0.0.1"
__maintainer__ = "ICOS Carbon Portal, elaborated products team"
__email__ = ['info@icos-cp.eu', 'anders.dahlner@nateko.lu.se']
__status__ = "rc1"
__date__ = "2023-09-06"

import os
from datetime import datetime as dt
import time


def get_unique_filename(path_to_file: str,
                        date_stamp: bool = None,
                        datetime_stamp: bool = None,
                        debug: bool = None) -> str:
    """
        If the file path_to_file exists, then this function
        returns a path with a possibly modified file.

        If date_stamp or datetime_stamp is True, then the function will
        allways return a path with a modified file name.

        Moreover, the function will try to create parent directories of
        the path.

        Might raise OSError, PermissionError or FileNotFoundError
        depending on os-access and validation of the suggested name.

        Input
        _____
        - path_to_file: str
                The path to a file to be created.
        - date_stamp: bool
                Default = False
                If True, a date string of the form "_YYYYMMDD_i",
                where "i" is a counter, will be inserted in
                front of the file extension.
        - datetime_stamp: bool
                Default = False
                If True, a datetime string of the form "_YYYYMMDD_hhmmss",
                will be added to the file-name.
                datetime_stamp will override the date_stamp input.

        Output
        ______
        - possibly modified relative path to file

        Examples
        --------
        In these examples we have path_to_file = 'my_files/my_file'.
            1.  If neither the directory 'my_files' nor the file 'my_file'
                exists, then
                    get_unique_filename(path_to_file)
                will try to create the directory 'my_files' and return
                    'my_files/my_file'
                raises OSError, PermissionError or FileNotFoundError
                depending on os-access and validation of the suggested name.
            2.  Suppose the directory 'my_files' exists but not the file
                'my_file', then
                    get_unique_filename('my_files/my_file')
                will return
                    'my_files/my_file'
            3.  Suppose the directory 'my_files' exists and contains a file
                named 'my_file.ext' and a file named 'my_file_1.ext',
                then
                    get_unique_filename('my_files/my_file.ext')
                will return
                    my_files/my_file_2.ext'
            4. Suppose the directory 'my_files' exists, but not the file
                named 'my_file.ext', then
                    get_unique_filename('my_files/my_file.ext',
                                        date_stamp=True)
                will return
                    my_files/my_file_20230920_1.ext'
                Even though the name was unique (her, of course, we assume the
                date is 2023-09-20).
            5.  Suppose the directory 'my_files' exists, and contains a file
                named 'my_file_20230920_1.ext', then
                    get_unique_filename('my_files/my_file.ext',
                                        date_stamp=True)
                will return
                    'my_files/my_file_20230920_2.ext'
        """

    debug = debug if isinstance(debug, bool) else False
    date_stamp = date_stamp if isinstance(date_stamp, bool) else False
    datetime_stamp = datetime_stamp if isinstance(datetime_stamp, bool) else False
    
    if debug:
        print(f'get_unique_filename - inputs'
              f'\n\t path_to_file ={path_to_file}'
              f'\n\t date_stamp = {date_stamp}'
              f'\n\t datetime_stamp = {datetime_stamp}')
    if not isinstance(path_to_file, str):
        raise AttributeError(f'Expected: a path like string tex_file, '
                             f'received:  {type(path_to_file)}.')

    path, file = os.path.split(path_to_file)
    if not os.path.isdir(path):
        path = makedirs_mod(path)
    temp_path_to_file = os.path.join(path, file)
    if date_stamp or datetime_stamp or os.path.exists(temp_path_to_file):
        file_name, file_ext = os.path.splitext(file)
        i = 1
        while True:
            if datetime_stamp:
                stamp = dt.now().strftime('%Y%m%d_%H-%M-%S')
            elif date_stamp:
                stamp = f'{dt.now().strftime("%Y%m%d")}_{i}'
            else:
                stamp = i
            temp_name = f'{file_name}_{stamp}{file_ext}'
            temp_path = os.path.join(path, temp_name)
            if not os.path.exists(temp_path):
                break
            elif datetime_stamp:
                time.sleep(1)
            elif i > 100:
                raise OSError(f'Please clean up the directory {path}.')
            i += 1
    else:
        temp_path = temp_path_to_file

    return os.path.relpath(temp_path)


def makedirs_mod(dir_str: str) -> str:
    """
        Creates a valid path out of `dir_str` such that
        1.  If there is a file with the same name as a
        directory in the path, then the name of that
        directory will get a counter at the end.
        2.  The function returns a perhaps modified path.
        This is similar to `os.makedirs`, however `os.makedirs(path)`
        has no return value and will raise a `FileExistsError`
        in case a subdirectory in the path exists as a file or link.

        Might raise OSError, PermissionError or FileNotFoundError
        depending on os-access and validation of the suggested name.

        Inputs
        ______
        - dir_str: str
                An pathlike string
        Output
        ______
        - possibly modified path
    """

    if not isinstance(dir_str, str):
        raise TypeError('Expected a non-empty path like string. '
                        f'\nReceived: `dir_str = {dir_str}` of '
                        f'`type = {type(dir_str)}`.')
    elif os.path.isdir(dir_str) or dir_str == '':
        out_path = dir_str
    else:
        head, tail = os.path.split(dir_str)
        if head and not os.path.isdir(dir_str):
            head = makedirs_mod(head)
        temp_path = os.path.join(head, tail)
        if os.path.isdir(temp_path):
            out_path = temp_path
        elif not os.path.exists(temp_path):
            os.mkdir(temp_path)
            out_path = temp_path
        else:
            i = 0
            while True:
                tail_i = f'{tail}_{i}'
                temp_path_i = os.path.join(head, tail_i)
                if not os.path.exists(temp_path_i):
                    os.mkdir(temp_path_i)
                    out_path = temp_path_i
                    break
                elif os.path.isdir(temp_path_i):
                    out_path = temp_path_i
                    break
                elif i > 10:
                    raise Exception(f'Unexpected error in the a call to '
                                    f'makedirs_mod() with the path-parameter '
                                    f'{dir_str}.')
                else:
                    i += 1
    return os.path.relpath(out_path)
