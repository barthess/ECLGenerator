#!/usr/bin/python
# -*- coding: utf8 -*-

import tabular as tb

import prepare
from globalvars import *


def columnwider(narrow_tab): #{{{
    """ Функция для расширения столбцов

    Принимает обычную таблицу, возвращает "раздутую"

    Из-за недоработок класса tabular колонки не могут расширяться динамически,
    поэтому на придется заранее вставить в конец файла поля заведомо
    бОльшей ширины.
    """
    # crate fake row
    first_row = narrow_tab[:1] # возьмем первый ряд для определения типа колонок
    empty_tuple = ()

    for i in first_row.dtype.names:
        if (type(first_row[i][0]).__name__) == 'string_':
            empty_tuple += (column_strut,)
        else:
            empty_tuple +=('',)

    wide_row = tb.tabarray(records=(empty_tuple,), names=list(first_row.dtype.names))

    # now we have table from one empty wide row
    # stack them to input table
    wide_tab = narrow_tab.rowstack([wide_row])

    # for now wide row is unnecessary
    # remove them
    wide_tab = wide_tab[:-1]

    return wide_tab
#}}}

def deleterow(input_tab, m): #{{{
    """ Функция удаления рядов из таблицы.

    Принимает входную таблицу и номер ряда, который надо удалить.

    Возвращает таблицу без указанного ряда.

    Удалить напрямую нельзя, зато можно откусить 2 куска,
    а потом склеить их вместе.
    """
    if m == 0:
        return input_tab[1:]
    elif m == len(tmp_tab):
        return input_tab[:-1]
    else:
        aa = input_tab[:m]
        bb = input_tab[(m+1):]

    aa = aa.rowstack(bb)
    aa = columnwider(aa) # раздуем таблицу

    return aa
#}}}


