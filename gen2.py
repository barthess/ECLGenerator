#!/usr/bin/python
# -*- coding: utf8 -*-

# TODO:

# единицы измерения номиналов при создании пикадовой схемы писать строго обязательно:
# (kOhm, MOhm, pF). При задании номинала конденсатора в P-CAD писать в следующем
# порядке: вольтаж, емкость, процентность использовать исключительно латиницу:
# uF, V

# Сжимать позиционные обозначения по горизонтали, только если одно из них
# перевалило за 10

# Функция pe3 содержит данные, почти готовые для создания спецификации. Надо
# их или временно сохранить и потом передать дальше, или вынести это в одну
# (несколько?) внешнюю функцию



#print tab.dtype.names


import string
import re
import os
import tabular as tb
from operator import itemgetter # for sort() and sorted()
import argparse
import sys

import prepare
from globalvars import *


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
    aa = prepare.columnwider(aa) # раздуем таблицу

    return aa
#}}}
def savelatex(filename, array): #{{{
    """ Функция сохранения таблицы в файл.

    Принимает имя выходного файла и таблицу, которую надо сохранить

    Не возвращает ничего

    Функция сохранения, встроенная в tabular, вписывает названия колонок в
    первую строку выходного файла. Нам это не подходит. Придется удалять уже
    после сохранения файла на диск.
    """

    array.saveSV('table.tmp', delimiter='&')

    f = open('table.tmp','r')
    aa = f.readlines()
    aa = aa[1:]
    f.close()

    f = open(filename,'w')
    m = 0
    while m < len(aa):
        f.write(aa[m])
        m += 1
    f.close()

    os.remove('table.tmp')
#}}}
def pe3(db): #{{{
    """ Создание таблицы для перечня элементов.  """

    # корпус и номинал вставим в скобках
    m = 0
    while m < len(db):
        db['Part Num'][m] += ' (' + db['Package'][m]
        if db['Value'][m] != '':
            db['Part Num'][m] += ' ' + db['Value'][m] + ')'
        else:
            db['Part Num'][m] += ')'
        db['Package'][m] = db['VID'][m] + ' ' + db['Vendor Part Num'][m]
        m+=1
    # remove unnecessary (now) columns
    db = db.deletecols(['Country of Origin', 'Unit Price', 'Value', 'VID', 'Vendor Part Num', 'Mfg Name'])


    def aggregate_items(tab, i, n):#{{{
        """ собирает пачку позиционных обозначений в одно поле
        Принимает:
            таблицу, в которой надо искать
            позицию, с которой надо искать
            количество одинаковых элементов"""
        if n == 1:
            return tab[i][0] + str(tab[i][1])
        elif n == 2:
            return tab[i][0] + str(tab[i][1]) + ', ' + tab[i+1][0] + str(tab[i+1][1])
        else:
            #TODO: replace 3 dots by latex symbol
            return tab[i][0] + str(tab[i][1]) + '...' + tab[i+n-1][0] + str(tab[i+n-1][1])
        #}}}
    def getslice(tab, i, st):#{{{
        """ Функция выкусывает срез строк с одинаковыми значениями в столбце
        Принимает:
            таблицу
            номер элемента, с которого надо начинать поиск
            строку с именем столбца, в котором производится поиск
        Возвращает:
            таблицу, содержащую срез """
        n = 0
        # print tab.dtype.names
        current_item = tab[i][st]
        while (i+n < len(tab)) and (current_item == tab[i+n][st]):
            n += 1
        return tab[i:i+n]
        #}}}
    def newpe3tab():#{{{
        """ Создает пустую таблицу для перечня элементов и добавляет в нее распорку """
        pe3tab_names = ['Part','Item','Quantity','Note',]
        pe3tab_formats = '|S1024,|S1024,|S1024,|S1024'
        pe3tab_cnt = 0 # текущая позиция в выходном массиве
        tab = tb.tabarray(shape=(0,),names=pe3tab_names,formats=pe3tab_formats)
        fakestr = 1024*'x'
        tab = tab.addrecords((fakestr, fakestr, fakestr, fakestr))
        return tab
        #}}}
    def compact_partslice(partslice):#{{{
        pe3tab = newpe3tab()

        i = 0
        single = False
        part = partslice[0]['Part']
        while (i < len(partslice)):
            itemslice = getslice(partslice, i, 'Part Num')
            parts = aggregate_items(itemslice, 0, len(itemslice))
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
        pe3tab = deleterow(pe3tab, 0)
        return (pe3tab, single, part)
        #}}}


    # create brand new table for pe3
    pe3tab = newpe3tab()

    i = 0
    while (i < len(db)):
        partslice = getslice(db, i, 'Part')
        i += len(partslice)
        p = compact_partslice(partslice)
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
        print pe3tab['Part'][i]
        i += 1

    # удалим ряд-распорку
    pe3tab = deleterow(pe3tab, 0)
    print pe3tab.dtype.names

    return pe3tab
#}}}



# command line parser {{{
parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Usage text
        description=('''\
------------------------ P-CAD section ---------------------------------------

Open schematic design in P-CAD. Go to menu File -> Reports.
You will see configuration dialog. Tune them.

Report destination: File
Style Format: Separated List
List Separator: &
Reports to generate: check only "Attributes (atr)"

Press "Customize"
  On tab "Format":
    Ensure that "Include Column Header" is checked (by default is checked)
  On tab "Selection":
    Chose needed component attributes (all by default)
  On tab "Sort":
    "Selected Field" must be "RefDes" (by default)
  Other tabs leave as is.
  Press "OK"

On main dialog specify output filename
Press "Generate"

  Note: You may record all this actions to P-CAD macro, and call them later.

Now you have list of components.
Process generated list by this script.


------------------------ Script section --------------------------------------
'''))

parser.add_argument('input_file',
        metavar='filename',
        type=file,
        help='path to file, generated by P-CAD')

parser.add_argument('-p','--pe3',
        metavar='FILENAME',
        type=str,
        default='pe3_table.tex',
        help='save pe3 to %(metavar)s (default: %(default)s)')

parser.add_argument('-s','--spec',
        metavar='FILENAME',
        type=str,
        default='spec_table.tex',
        help='save specification to %(metavar)s (default: %(default)s)')

parser.add_argument('-b','--bill',
        metavar='FILENAME',
        type=str,
        default='bill_table.tex',
        help='save bill list to %(metavar)s (default: %(default)s)')

args = parser.parse_args()

# cleaning input file and reading it to table
# read input file to the buffer
raw_input_file = args.input_file.readlines()

out = open('cleaned_output.tmp','w')
out = open('cleaned_output.tmp','r+')

# delete empty lines and redundant quotes
for line in (raw_input_file):
    # использование в регулярках '$' тут почему-то не прокатывает
    # \r\n - виндовый конец строки, \n - юниксовый, так, на всякий случай
    if re.search('^[    ]*\r\n|^[    ]*\n', line) == None: # if string non empty
        line = re.sub('"','',line) # delete all quotes
        line = re.sub('[ ]*&[ ]*','&',line) # delete unneeded spaces
        # screaning latex special symbols
        line = re.sub('\\\\','\\\\textbackslash ',line)
        line = re.sub('%','\%',line)
        line = re.sub('_','\_',line)
        line = re.sub('#','\#',line)
        line = re.sub('\^','\^',line)
        line = re.sub('~','\~',line)
        line = re.sub('{','\{',line)
        line = re.sub('}','\}',line)
        line = re.sub('\$','\$',line)
        out.write(line)

# Hack!
# This line tells tabarray, that all columns contain string values
# not a numbers. Remove it after loading file
last_line = re.sub('[\t]','fake\t',raw_input_file[0])
out.write(last_line)
out.close()

# reading file into array
raw = tb.tabarray(SVfile = "cleaned_output.tmp",delimiter = '\t')
raw = raw[:-1] # remove hack-line
raw = prepare.columnwider(raw)
tmp_tab = raw # create temporal array
os.remove("cleaned_output.tmp") # remove temporal file
#}}}


bd = prepare.prepare(raw)

# build component list PE3
pe3_array = pe3(bd)

# save table to file
savelatex(args.pe3, pe3_array)









# автоматический aggregate годится только для генерации спецификации
# aggregate rows
#def refdes_agg(i):
#   return i[0]
#
#tmp_tab = raw.aggregate(On=['Title','Type','SType','Value','Docum','Addit','Note','OrderCode'])
#
#print tmp_tab
#




