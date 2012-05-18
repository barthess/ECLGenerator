#!/usr/bin/python
# -*- coding: utf8 -*-

import re
import tabular as tb

from globalvars import *
import utils


#print tab.dtype.names

def __newpe3tab():#{{{
    """ Создает пустую таблицу для перечня элементов и добавляет в нее распорку """
    pe3tab_names = ['Part','Item','Quantity','Note',]
    pe3tab_formats = '|S1024,|S1024,|S1024,|S1024'
    pe3tab_cnt = 0 # текущая позиция в выходном массиве
    tab = tb.tabarray(shape=(0,),names=pe3tab_names,formats=pe3tab_formats)
    fakestr = 1024*'x'
    tab = tab.addrecords((fakestr, fakestr, fakestr, fakestr))
    return tab
    #}}}
def __aggregate_items(tab, i, n):#{{{
    """ собирает пачку строк с одинаковыми элементами в одну
    Принимает:
        таблицу, в которой надо искать
        позицию, с которой надо искать
        количество одинаковых элементов"""
    if n == 1:
        return tab[i][0] + str(tab[i][1])
    elif n == 2:
        return tab[i][0] + str(tab[i][1]) + ', ' + tab[i+1][0] + str(tab[i+1][1])
    else:
        return tab[i][0] + str(tab[i][1]) + '...' + tab[i+n-1][0] + str(tab[i+n-1][1])
    #}}}
def __getslice(tab, i, st):#{{{
    """ Функция выкусывает срез строк с одинаковыми значениями в каком-либо столбце
    Принимает:
        таблицу
        номер элемента, с которого надо начинать поиск
        строку с именем столбца, в котором производится поиск
    Возвращает:
        таблицу, содержащую срез """
    n = 0
    # получим условное обозначение типа элемента (С, R, VT...)
    current_item = tab[i][st]
    if current_item != 'D' and current_item != 'DD' and current_item != 'DA':
        while (i+n < len(tab)) and (current_item == tab[i+n][st]):
            n += 1
        return tab[i:i+n]
    else:
        # микросхемы придется обрабатывать отдельно, потому что
        # не смотря на разные позиционные обозначения (DD, D, DA)
        # у них должна быть одна единственная шапка "Микросхемы"
        while (i+n < len(tab)) and (tab[i+n][st][0] == 'D'):
            n += 1
        return tab[i:i+n]
    #}}}
def __compact_partslice(partslice):#{{{
    """ Сжимает срез с одинаковыми элементами в одну строку """
    pe3tab = __newpe3tab()

    i = 0
    single = False
    part = partslice[0]['Part']
    while (i < len(partslice)):
        itemslice = __getslice(partslice, i, 'Part Num')
        parts = __aggregate_items(itemslice, 0, len(itemslice))
        i += len(itemslice)
        if len(itemslice) == len(partslice):
            single = True
        else:
            single = False

        item = itemslice[0]['Part Num']
        quantity = len(itemslice)
        package = itemslice[0]['Package']
        pe3tab = pe3tab.addrecords((parts, item, str(quantity), package + '\\tabularnewline'))

    # удалим ряд-распорку
    pe3tab = utils.deleterow(pe3tab, 0)
    return (pe3tab, single, part)
    #}}}
def __mergecolumns(db):#{{{
    """ Собирает данные из нужных колонок в нужном порядке в колонку Наименование """
    # корпус и номинал вставим в скобках
    m = 0
    while m < len(db):
        description = ''
        if db['Package'][m] != '':
            description += db['Package'][m] + ' '
        if db['Value'][m] != '':
            description += db['Value'][m] + ' '
        if description != '':
            description = description[0:-1]
            description = ' (' + description + ')'
        if db['Mfg Name'][m] != '':
            description = db['Mfg Name'][m] + ' ' + description
        if description != '':
            db['Part Num'][m] += ' ' + description
        m+=1
    # remove unnecessary (now) columns
    db = db.deletecols(['Country of Origin', 'Unit Price', 'Value', 'VID', 'Vendor Part Num', 'Mfg Name'])
    return db
    #}}}

def pe3(db): #{{{
    """ Создание таблицы для перечня элементов.  """

    # create brand new table for pe3
    pe3tab = __newpe3tab()

    db = __mergecolumns(db)

    i = 0
    while (i < len(db)):
        partslice = __getslice(db, i, 'Part')
        i += len(partslice)
        p = __compact_partslice(partslice)
        pe3piece = p[0]
        if p[1] is True:
            blockname = component_des[p[2]][0]
            n = pe3piece['Quantity'][0]
            parts = pe3piece['Part'][0]
            item = pe3piece['Item'][0]
            pe3tab = pe3tab.addrecords((str(parts), blockname + ' ' + item, str(n), pe3piece['Note'][0] + '*'))
            pe3tab = pe3tab.addrecords(('','','','\\tabularnewline*'))
            pe3tab = pe3tab.addrecords(('','','','\\tabularnewline'))
        else:
            blockname = component_des[p[2]][1]
            pe3tab = pe3tab.addrecords(('','\\centering{' + blockname + '}','','\\tabularnewline*'))
            pe3tab = pe3tab.addrecords(('','','','\\tabularnewline*'))
            pe3piece['Note'][0] += '*'

            if len(pe3piece) == 2:
                pe3piece['Note'][-1] += '*'
            elif len(pe3piece) > 2:
                pe3piece['Note'][-1] += '*'
                pe3piece['Note'][-2] += '*'

            pe3tab = pe3tab.rowstack(pe3piece)
            pe3tab = pe3tab.addrecords(('','','','\\tabularnewline*'))
            pe3tab = pe3tab.addrecords(('','','','\\tabularnewline'))
    i = 0
    while i < len(pe3tab):
        # заключим Part в хитрый бокс
        pe3tab['Part'][i] = '\ESKDsmartScaleBox{\\argi -2\\tabcolsep}{' + pe3tab['Part'][i] + '}'
        i += 1

    # удалим ряд-распорку
    pe3tab = utils.deleterow(pe3tab, 0)

    return pe3tab
#}}}


