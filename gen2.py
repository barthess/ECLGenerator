#!/usr/bin/python
# -*- coding: utf8 -*-

# TODO:

# единицы измерений при создании пикадовой схемы писать строго обязательно:
# kOhm, MOhm, pF При задании номинала конденсатора в P-CAD писать в следующем
# порядке: вольтаж, емкость, процентность использовать исключительно латиницу:
# uF, V

# Сжимать позиционные обозначения по горизонтали, только если одно из них
# перевалило за 10

# вставить обработку исключений при подгрузке питоновых модулей, подсказывать,
# чего не хватает

# Функция pe3 содержит данные, почти готовые для создания спецификации. Надо
# их или временно сохранить и потом передать дальше, или вынести это в одну
# (несколько?) внешнюю функцию


import string
import re
import os
import tabular as tb
from operator import itemgetter # for sort() and sorted()
import argparse
import sys

# data structuers {{{
# preparing some data structures
# log file
logfile = open('error.log','w')

# Некоторые константы
# ширина фейковых полей для поддержания ширины колонок
column_strut = ' ' * 1024

# дефолтный список колонок
# данный список содержит правильные названия колонок, как их генерит P-CAD
# они должны идти в том порядке, как должны появляться перечне
column_names = ['Part', 'PartN', 'Part Num', 'Value', 'VID', 'Vendor Part Num', 'Mfg Name', 'Package', 'Country of Origin', 'Unit Price']
column_num = len(column_names)

# словарь для поиска по готовому массиву
#
# Тут хранятся все известные нам элементы. Если попадется неизвестный -
# скрипт прервет выполнение и предложит пользователю добавить сюда
# неизвестный элемент
#
# Как заполнять:
# 'key' : ['ед. число','мн. число','смещение','количество']
#
# Смещение и количество по умолчанию равны -1, они будут заполняться
# скриптом во время анализа главной таблицы.
component_des = {   'C' : ['Конденсатор','Конденсаторы',-1,-1], \
                    'E' : ['Перемычка','Перемычки',-1,-1], \
                    'R' : ['Резистор','Резисторы',-1,-1], \
                    'D' : ['Микросхема','Микросхемы',-1,-1], \
                    'DA': ['Микросхема','Микросхемы',-1,-1], \
                    'DD': ['Микросхема','Микросхемы',-1,-1], \
                    'L' : ['Дроссель','Дроссели',-1,-1], \
                    'RK': ['Терморезистор','Терморезисторы',-1,-1], \
                    'RP': ['Резистор подстроечный','Резисторы подстроечные',-1,-1], \
                    'VD': ['Диод','Диоды',-1,-1], \
                    'XP': ['Вилка','Вилки',-1,-1], \
                    'XS': ['Розетка','Розетки',-1,-1], \
                    'Z' : ['Фильтр радиочастотный','Фильтры радиочастотные',-1,-1], \
                    'ZQ': ['Резонатор кварцевый','Резонаторы кварцевые',-1,-1], \
                    }
# Отдельно посортируем, потому что питоновый словарь выбирает
# элементы в случайном порядке
pos_names = sorted(component_des.keys())
# }}}
def prepare(x): # {{{
    """ Функция предварительной очистки и подготовки.

    """
    # remove '*' placeholders
    for i in x.dtype.names:
        m = 0
        while m < len(x):
            if x[i][m] == '*':
                x[i][m] = ''
            m+=1

    # split 'Part' column in two columns to simplify sorting
    parts = []
    parts_num = []
    # получим столбец цифр
    m = 0
    while m < len(x):
        parts_num.append(int(re.sub('[a-zA-Z]*','',x['Part'][m])))
        m += 1
    # в 'Part' запишем только буквы
    m = 0
    while m < len(x):
        x['Part'][m] = (re.sub('[0-9]*','',x['Part'][m]))
        m += 1
    # добавим столбец номеров
    tmp_tab = x.addcols([parts_num], names='PartN')
    x = tmp_tab

    # remove rows with empty Part field
    m = 0
    deleted = False
    while m < len(x):
        if x['Part'][m] == '':

            log_msg = 'deleted: '
            for i in column_names:
                log_msg += str(x[i][m])
            logfile.write(log_msg + '\n')

            x = deleterow(x,m)
            deleted = True
            m -= 1
        m += 1
    if deleted:
        print '*** Some elements deleted, because they have no Part field (see:',logfile.name,')'

    # remove columns with wrong name
    m = 0
    flag = 0
    for i in x.dtype.names:
        while m < column_num:
            if column_names[m] == i: # raise flag if any match
                flag = 1
            m+=1
        if flag == 0:
            print '*** deleting wrong column', i
            tmp_tab = x.deletecols([i])
        m = 0
        flag = 0

    # create empty column
    empty_col = []
    m = 0
    while m < len(x):
        empty_col.append('')
        m+=1

    # add empty columns if needed
    col_names = x.dtype.names
    col_num = len(col_names)
    m = 0
    flag = 0
    for i in column_names:
        while m < col_num:
            if col_names[m] == i: # raise flag if any match
                flag = 1
            m+=1
        if flag == 0:
            print '*** adding empty column', i
            tmp_tab = x.addcols([empty_col],names=[i])
        m = 0
        flag = 0
    x = tmp_tab # now x contain only suitable columns

    # stack columns 1 by 1 in right order
    tmp_tab = x[['Part']] # save to tmp_tab first column
    m = 1
    while m < column_num:
        z = tmp_tab.colstack(x[[column_names[m]]])
        tmp_tab = z
        m+=1
    x = z # now x contains columns in right order

    # sort by part name
    x.sort(order=['Part'])

    # add russian LaTeX quotas to column 'Mfg Name'
    m = 0
    while m < len(x):
        if re.search('^[    ]*$', x['Mfg Name'][m]) == None: # если поле НЕ пустое
            x['Mfg Name'][m] = ('<<' + x['Mfg Name'][m] + '>>')
        m+=1

    return x
#}}}
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
def process_value(s, part): #{{{
    """ Приводит поле Value к каноничному виду.

    Принимает строку и тип элемента, напр. C, L, R.
    Тип элемента нужен для выбора правильных регулярок.

    Возвращает обработанную строку.
    """

    # регулярные выражения для поиска номиналов
    tolerance =     re.compile('[0-9]*[.,]*[0-9]*[ ]*\\\\%')
    capacitance =   re.compile('[0-9]*[.,]*[0-9]*[ ]*[umnp]?F')
    current =       re.compile('[0-9]*[.,]*[0-9]*[ ]*[num]?A')
    frequency =     re.compile('[0-9]*[.,]*[0-9]*[ ]*[kMG]?Hz')
    inductance =    re.compile('[0-9]*[.,]*[0-9]*[ ]*[unm]?H')
    power =         re.compile('[0-9]*[.,]*[0-9]*[ ]*[umk]?W')
    resistance =    re.compile('[0-9]*[.,]*[0-9]*[ ]*[mkM]?Ohm')
    voltage =       re.compile('[0-9]*[.,]*[0-9]*[ ]*[mkM]?[Vv]')

    def pseudo_translate(st):
        st = re.sub('F','Ф',st)
        st = re.sub('A','А',st)
        st = re.sub('Hz','Гц',st)
        st = re.sub('H','Гн',st)
        st = re.sub('W','Вт',st)
        st = re.sub('Ohm','Ом',st)
        st = re.sub('[Vv]','В',st)

        st = re.sub('p','п',st)
        st = re.sub('n','н',st)
        st = re.sub('u','мк',st)
        st = re.sub('m','м',st)
        st = re.sub('k','к',st)
        st = re.sub('M','М',st)
        st = re.sub('G','Г',st)
        return st

    def clean(oldstring, *args): # вспомогательная функция {{{
        """ Обработка строки регулярками.

        Принимает строку, которую надо обработать и скомпилированные
        регулярки, которыми надо обрабатывать. Порядок регулярок имеет
        значение - он определяет порядок следования значений номиналов в
        выходной строке. Куски, соответствующие регуляркам выкусываются из
        входной строки и из этих кусков составляется выходная строка.  Остатки
        входной строки (то, что не попало ни в одну регулярку) прилепляется в
        конец.

        Возвращает обработанную строку.
        """
        newstring = ''
        s1 = ''
        for regexp in (args):
            t1 = regexp.findall(oldstring)
            if len(t1) > 0:
                # вставим нужные отбивки
                s1 = re.sub('([0-9]*)([.,]*)([0-9]*)([ ]*)([a-zA-Z\\\\%]*)','\\1\\2\\3",\\5',t1[0])
                # заменить точку на запятую
                s1 = re.sub('([0-9]*)[.,]([0-9]*",)','\\1,\\2',s1)
                # вставить ведущий ноль
                s1 = re.sub('^,','0,',s1)
                # перевод на русский
                s1 = pseudo_translate(s1)
                newstring += (s1 + ' ')

            # теперь newstring содержит все нужные нам подстроки в нужном порядке
            # надо удалить их из исходной строки
            oldstring = regexp.sub('',oldstring)

        # остатки старой строки прилепить в конец новой
        # TODO: если осталось что-то кроме пробелов выдать варнинг
        #if re.search('[^     ]*',oldstring)
        newstring = newstring + oldstring
	# снабдим процентаж знаком плюс-минус (\textpm)
	newstring = re.sub('([0-9]*[,]*[0-9]*",\\\\%)',' {\\\\textpm}",\\1',newstring)
        # вычистим из конца пробелы, которые остались от старой строки
        newstring = re.sub('[	]*$','',newstring)
	return newstring
    #}}}

    # логика выбора нужных регулярок в зависимости от типа элемента
    if part ==    'C':
        s = clean(s, capacitance, tolerance, voltage)
    elif part ==  'L':
        s = clean(s, inductance, tolerance, current)
    elif (part == 'R') | (part == 'RK') | (part == 'RP'):
        s = clean(s, resistance, tolerance, power)
    elif part == 'ZQ':
        s = clean(s, frequency, tolerance)
    else: # обработчик лажи
        unknown_element = True
        for i in pos_names:
            if part == i:
                unknown_element = False
        if unknown_element:
            # аварийное завершение, скрипт не знает такого элемента
            print 'Something goes wrong. I don\'t know element type:',part
            quit()

    # Дополнительные вычистки
    # тут же можно поудалять лишних пробелов
    s = re.sub('[ ]*",[ ]*','",',s)
    s = re.sub('^[ ]*|[ ]*$','',s)
    s = re.sub('[ ]+',' ',s)

    # а так же случайно попавшие двойные последовательности вроде ",",
    s = re.sub('",+','",',s)
    return s
#}}}
def mboxing(array, *columns): #{{{
    """ Заключение нужных ячеек в \mbox{}.

    Принимает имя таблицы и имена колонок, которые надо заключить в mbox.

    Возвращает обработанную таблицу.
    """
    if len(columns) == 0:
        return(array)

    m = 0
    i = ''
    while m < len(array):
        for i in (columns):
            if not re.match('^[ ]*$', array[i][m]):
                array[i][m] = '\mbox{' + array[i][m] + '}'
        m += 1
    return(array)
#}}}
def pe3(intab): #{{{
    """ Создание таблицы для перечня элементов.
    """
    # process Value column
    m = 0
    while m < len(intab):
        intab['Value'][m] = process_value(intab['Value'][m], intab['Part'][m])
        m += 1

    # enclose in mbox
    intab = mboxing(intab, 'Part Num','Value', 'VID', 'Vendor Part Num', 'Mfg Name', 'Package', 'Country of Origin')

    # merge columns
    m = 0
    while m < len(intab):
        intab['Part Num'][m] += intab['Value'][m] + ' ' + intab['Mfg Name'][m] + intab['VID'][m] + intab['Vendor Part Num'][m]
        m+=1

    # remove unnecessary columns
    intab = intab.deletecols(['Country of Origin', 'Unit Price', 'Value', 'VID', 'Vendor Part Num', 'Mfg Name'])

    # create brand new table for pe3
    pe3tab_names = ['Part','Item','Quantity','Note',]
    pe3tab_formats = '|S1024,|S1024,|S1024,|S1024'
    pe3tab_cnt = 0 # текущая позиция в выходном массиве
    pe3tab = tb.tabarray(shape=(0,),names=pe3tab_names,formats=pe3tab_formats)


    def ismultiple(tab, i):
        """ Проверяет, во множественном или одиночном числе надо писать наименвоание
        Принимает:
            таблицу, в которой надо искать
            элемент, с которого надо начинать поиск """

        s0 = tab[i][0]

        try:
            snext = tab[i+1][0]
        except IndexError:
            return False

        if s0 != snext:
            return False
        else:
            return True

    def calcmultiple(tab, i):
        """ Считает количество одинаковых элементов и возвращает их количество.
        Принимает:
            таблицу, в которой надо искать
            элемент, с которого надо начинать поиск """
        n = 1
        s0 = tab[i][2]
        while (i < len(tab)):
            try:
                snext = tab[i+1][2]
            except IndexError:
                return 1

            if s0 != snext:
                return n
            n += 1
            i += 1

    def aggregate_parts(tab, i, n):
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
            return tab[i][0] + str(tab[i][1]) + '...' + tab[i+n][0] + str(tab[i+n][1])


    # определяем, у нас один элемент, или больше
    i = 0
    n = 0
    while (i < len(intab)):
        key = intab[i][0]
        n = calcmultiple(intab, i)

        if ismultiple(intab, i): # если деталей больше одной
            blockname = component_des[key][1]
            pe3tab = pe3tab.addrecords(('','','','\\tabularnewline'))
            pe3tab = pe3tab.addrecords(('','\\centering{' + blockname + '}','','\\tabulrnewline*'))
            pe3tab = pe3tab.addrecords(('','','','\\tabulrnewline*'))
            item = intab[i][2]
        else:
            blockname = component_des[key][0]
            pe3tab = pe3tab.addrecords(('','','',''))
            item = blockname + ' ' + intab[i][2]

        parts = aggregate_parts(intab, i, n)
        pe3tab = pe3tab.addrecords((parts, item, str(n), intab[i][3] + '\\tabularnewline'))
        i += n

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
	out.write(line)

# Hack!
# This line tells tabarray, that all columns contain string values
# not a numbers. Remove it after loading file
last_line = re.sub('[\t]','fake\t',raw_input_file[0])
out.write(last_line)
out.close()

# reading file into array
x = tb.tabarray(SVfile = "cleaned_output.tmp",delimiter = '\t')
x = x[:-1] # remove hack-line
x = columnwider(x)
tmp_tab = x # create temporal array
os.remove("cleaned_output.tmp") # remove temporal file
#}}}


x = prepare(x)

# build component list PE3
pe3_array = pe3(x)

# save table to file
savelatex(args.pe3, pe3_array)









# автоматический aggregate годится только для генерации спецификации
# aggregate rows
#def refdes_agg(i):
#   return i[0]
#
#tmp_tab = x.aggregate(On=['Title','Type','SType','Value','Docum','Addit','Note','OrderCode'])
#
#print tmp_tab
#




