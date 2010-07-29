#!/usr/bin/python
# -*- coding: cp1251 -*-

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

# preparing some data structures {{{

# log file{{{
logfile = open('error.log','w')
#}}}

# Некоторые константы {{{
# ширина фейковых полей для поддержания ширины колонок
column_strut = ' ' * 1024
#}}}

# дефолтный список колонок {{{
# данный список содержит правильные названия колонок, как их генерит P-CAD
# они должны идти в том порядке, как должны появляться перечне
column_names = ['RefDes', 'RefDesNum', 'Title', 'Type', 'SType', 'Value', 'Docum', 'Addit', 'Note', 'OrderCode']
column_num = len(column_names)
#}}}

# словарь для поиска по готовому массиву {{{
# 
# Тут хранятся все известные нам элементы. Если попадется неизвестный -
# скрипт прервет выполнение и предложит пользователю добавить сюда
# неизвестный элемент
#
# Как заполнять:
# 'key' : ['ед. число','мн. число','смещение','количество']
#
# Смещение и количество по умолчанию равны -1, они будут заполняться
# во время анализа главной таблицы.
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
#}}}

#}}}


def column_wide(narrow_tab): #{{{
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
    aa = column_wide(aa) # раздуем таблицу

    return aa
#}}}


def save_to_file(filename, array): #{{{
    """ Функция сохранения таблицы в файл.

    Принимает имя выходного файла и таблицу, которую надо сохранить

    Не возвращает ничего

    Функция сохранения, встроенная в tabular, вписывает названия колонок в
    первую строку выходного файла. Нам это не подходит. Придется удалять уже
    после сохранения файла на диск.
    """

    # taking basename from full path to file
    #s = (re.sub('.*/|\.[^.]*$','',args.input_file.name) + '_table_pe3.tex')

    # save to temporal file
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


def process_value(s, refdes): #{{{
    """ Приводит поле Value к каноничному виду.

    Принимает строку и тип элемента, напр. C, L, R.
    Тип элемента нужен для выбора правильных реглярок.

    Возвращает обработанную строку.
    """

    # регулярные выражения для поиска номиналов{{{
    tolerance =     re.compile('[0-9]*[.,]*[0-9]*[ ]*\\\\%')

    capacitance =   re.compile('[0-9]*[.,]*[0-9]*[ ]*[umnp]?F')
    current =       re.compile('[0-9]*[.,]*[0-9]*[ ]*[num]?A')
    frequency =     re.compile('[0-9]*[.,]*[0-9]*[ ]*[kMG]?Hz')
    inductance =    re.compile('[0-9]*[.,]*[0-9]*[ ]*[unm]?H')
    power =         re.compile('[0-9]*[.,]*[0-9]*[ ]*[umk]?W')
    resistance =    re.compile('[0-9]*[.,]*[0-9]*[ ]*[mkM]?Ohm')
    voltage =       re.compile('[0-9]*[.,]*[0-9]*[ ]*[mkM]?V')
    #}}}

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
                # FIXME: тут уместно будет перевести на русский
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

    # логика выбора нужных регулярок в зависимости от типа элемента {{{
    if refdes ==    'C':
        s = clean(s, capacitance, tolerance, voltage)
    elif refdes ==  'L':
        s = clean(s, inductance, tolerance, current)
    elif (refdes == 'R') | (refdes == 'RK') | (refdes == 'RP'):
        s = clean(s, resistance, tolerance, power)
        # FIXME: сопротивление можно обозначать \textohm
        #s = re.sub('Ohm','{\\\\textohm}',s)
    elif refdes == 'ZQ':
        s = clean(s, frequency, tolerance)
    else: # обработчик лажи
        unknown_element = True
        for i in pos_names:
            if refdes == i:
                unknown_element = False
        if unknown_element:
            # аварийное завершение, скрипт не знает такого элемента
            print 'Something goes wrong. I don\'t know element type:',refdes
            quit()
    #}}}

    # Дополнительные вычистки{{{
    # тут же можно поудалять лишних пробелов
    s = re.sub('[ ]*",[ ]*','",',s)
    s = re.sub('^[ ]*|[ ]*$','',s)
    s = re.sub('[ ]+',' ',s)

    # а так же случайно попавшие двойные последовательности вроде ",",
    s = re.sub('",+','",',s)
    #}}}

    return s
#}}}


def prepare(x): # {{{
    """ Функция предварительной очистки и подготовки.

    """
    # split 'RefDes' column in two columns {{{
    refdes = []
    refdes_num = []
    # получим столбец цифр
    m = 0
    while m < len(x):
        refdes_num.append(int(re.sub('[a-zA-Z]*','',x['RefDes'][m])))
        m += 1
    # в RefDes запишем только буквы
    m = 0
    while m < len(x):
        x['RefDes'][m] = (re.sub('[0-9]*','',x['RefDes'][m]))
        m += 1
    # добавим столбец номеров
    tmp_tab = x.addcols([refdes_num], names='RefDesNum')
    x = tmp_tab
    #}}}

    # remove rows with empty RefDes{{{
    m = 0
    deleted = False
    while m < len(x):
        if x['RefDes'][m] == '':

            log_msg = 'deleted: '
            for i in column_names:
                log_msg += str(x[i][m])
            logfile.write(log_msg + '\n')

            x = deleterow(x,m)
            deleted = True
            m -= 1
        m += 1
    if deleted:
        print '*** Some elements deleted, because they have no RefDes (see:',logfile.name,')'
    #}}}

    # remove wrong columns{{{
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
    #}}}

    # create empty column{{{
    empty_col = []
    m = 0
    while m < len(x):
        empty_col.append('')
        m+=1
    #}}}

    # add empty columns if needed {{{
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

#}}}

    # stack columns 1 by 1 in right order{{{
    tmp_tab = x[['RefDes']] # save to tmp_tab first column
    m = 1
    while m < column_num:
        z = tmp_tab.colstack(x[[column_names[m]]])
        tmp_tab = z
        m+=1
    x = z # now x contain columns in right order 
    #}}}

    # add russian LaTeX quotas to column 'Addit'{{{
    m = 0
    while m < len(x):
        if re.search('^[    ]*$', x['Addit'][m]) == None: # если поле НЕ пустое
            x['Addit'][m] = ('<<' + x['Addit'][m] + '>>')
        m+=1
    #}}}

    # screaning latex special symbols{{{
    # this was moved here because & is input delimeter
    x.replace('&','\&',strict=False, cols=['RefDes', 'Title', 'Type', \
                                            'SType', 'Value', 'Docum', \
                                            'Addit', 'Note', 'OrderCode'])
    #}}}

    return x
#}}}


def indexing(array): #{{{
    """ Функция поиска строк с элементами одного типа.

    Фактически, заполнение последних двух столбцов таблицы position_names
    """
    for key in pos_names:
        m = 0
        i = 0
        while m < len(array):
            if array['RefDes'][m] == key:
                i += 1
                if component_des[key][2] == -1:
                    component_des[key][2] = m # смещение
            m += 1
        component_des[key][3] = i # количество

    #searching for unknown types of element
    m = 0
    fail = False
    for refdes in array['RefDes']:
        known = False
        for key in pos_names:
            if refdes == key:
                known = True
        if not known:
            fail = True
            print '!!! Unknown element type:', array['RefDes'][m] + str(array['RefDesNum'][m])
        m += 1
    if fail:
              #----------------- 78 dashes line ----------------------------------------------#
        print '\nEmergency stop.'
        print 'Possible reasons:'
        print '  - mistype in RefDes during P-CAD element creation;'
        print '  - it\'s correct new element but script don\'t know about them.'
        print 'If elements above are correct - add them manually to the \"component_des\"'
        print 'dictionary and run script again.'
        quit()
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


def pe3(pe3_in): #{{{
    """ Создание таблицы для перечня элементов.

    Ужос, а не функция!
    Надо переписать, повыносить, что можно во внешние функции
    """
    firstrun = True

    # process Value column
    m = 0
    while m < len(pe3_in):
        pe3_in['Value'][m] = process_value(pe3_in['Value'][m], pe3_in['RefDes'][m])
        m += 1

    # enclose in mbox
    pe3_in = mboxing(pe3_in,'Title','Type','SType','Value','Docum','Addit','Note')

    # merge columns
    m = 0
    while m < len(pe3_in):
        pe3_in['Title'][m] = pe3_in['Type'][m] + pe3_in['SType'][m] + ' ' + \
                pe3_in['Value'][m] + ' ' + \
                pe3_in['Docum'][m] + ' ' + \
                pe3_in['Addit'][m]
        m+=1

    # rename 'Title' column
    pe3_in.renamecol('Title','Item')

    # rename and clean 'Addit' columnt
    pe3_in.renamecol('Addit','Sum')
    m = 0
    while m < len(pe3_in):
        pe3_in['Sum'][m] = ''
        m += 1

    # remove unnecessary columns
    pe3_in = pe3_in.deletecols(['Type', 'SType', 'Value', 'Docum', 'OrderCode'])

    for key in pos_names: # Уплотнение рядов {{{
        # catch one RefDes
        component_slice = pe3_in[ component_des[key][2] : (component_des[key][2] + component_des[key][3]) ]

        # take first row
        tmp_tab = component_slice[:1]

        m = 0
        if len(component_slice) > 1:
            prev = component_slice['RefDes'][m] +   component_slice['Item'][m] +    component_slice['Note'][m]
            next = component_slice['RefDes'][m+1] + component_slice['Item'][m+1] +  component_slice['Note'][m+1]

            while m < (len(component_slice)-2):
                if next == prev:
                    # take next row
                    prev = next
                    next = component_slice['RefDes'][m+2] + component_slice['Item'][m+2] + component_slice['Note'][m+2]
                else: # сюда попадаем, если натыкаемся на незнакомую строку
                    # добавим эту незнакомую строку в tmp_tab
                    tmp_tab = tmp_tab.addrecords((component_slice['RefDes'][m+1], \
                            component_slice['RefDesNum'][m+1] - 1, \
                            component_slice['Item'][m+1], \
                            component_slice['Sum'][m+1], \
                            component_slice['Note'][m+1]))
                    # сместим RefDesNum на одну позицию назад, чтобы не терялись значения
                    tmp_tab['RefDesNum'][len(tmp_tab) - 2] = tmp_tab['RefDesNum'][len(tmp_tab) - 1]
                    # take next row
                    prev = next
                    next = component_slice['RefDes'][m+2] + component_slice['Item'][m+2] + component_slice['Note'][m+2]
                m += 1

            # по выходу из цикла поправим предпоследний ряд после смещения
            tmp_tab['RefDesNum'][len(tmp_tab) - 1] = component_slice['RefDesNum'][m+1] - 1

            # персонально обработаем последний ряд
            # либо добавиться новый, либо изменится RefDesNUm
            if next == prev:
                tmp_tab['RefDesNum'][len(tmp_tab)-1] = component_slice['RefDesNum'][m+1]
            else:
                tmp_tab = tmp_tab.addrecords((component_slice['RefDes'][m+1], \
                        component_slice['RefDesNum'][m+1], \
                        component_slice['Item'][m+1], \
                        component_slice['Sum'][m+1], \
                        component_slice['Note'][m+1]))
        #}}}

        # обновление поля RefDes {{{
        if len(tmp_tab) > 0:

            def scale(str):
                str = '\scalebox{0.75}[1]{' + str + '}'
                return str

            m = 0
            while m < len(tmp_tab):
                sum = 0
                if m == 0: # если мы в первом ряду
                    sum = int(tmp_tab['RefDesNum'][m])
                    if sum > 2:
                        refdes = key + '1' + '...' + key + str(tmp_tab['RefDesNum'][m])
                        refdes = scale(refdes)
                    if sum == 2:
                        refdes = key + '1' + ', ' + key + str(tmp_tab['RefDesNum'][m])
                        refdes = scale(refdes)
                    if sum == 1:
                        refdes = key + str(tmp_tab['RefDesNum'][m])
                        #refdes = scale(refdes)

                else:
                    sum = int(tmp_tab['RefDesNum'][m]) - int(tmp_tab['RefDesNum'][m-1])
                    if sum > 2:
                        refdes = key + str(tmp_tab['RefDesNum'][m-1]+1) + '...' + key + str(tmp_tab['RefDesNum'][m])
                        refdes = scale(refdes)
                    if sum == 2:
                        refdes = key + str(tmp_tab['RefDesNum'][m-1]+1) + ', ' + key + str(tmp_tab['RefDesNum'][m])
                        refdes = scale(refdes)
                    if sum == 1:
                        refdes = key + str(tmp_tab['RefDesNum'][m])
                        #refdes = scale(refdes)

                # if we have more then one item in first line
                if sum > 0:
                    tmp_tab['RefDes'][m] = refdes
                    tmp_tab['Sum'][m] = sum
                m += 1
        #}}}
        tmp_tab = tmp_tab.deletecols(['RefDesNum']) # remove unneeded column

        # add LaTeX new line symbol {{{
        if len(tmp_tab) > 0:
            m = 0
            last_col = tmp_tab.dtype.names[-1:][0]
            while m < len(tmp_tab):
                # may be better '\tabularnewline'?
                tmp_tab[last_col][m] = tmp_tab[last_col][m] + '\\\\'
                m += 1
            # first and last must be ends by non breakable symbols
            tmp_tab[last_col][0] = tmp_tab[last_col][0] + '*'
            if len(tmp_tab) > 1:
                tmp_tab[last_col][-1:] = tmp_tab[last_col][-1:][0] + '*'
            if len(tmp_tab) > 2:
                tmp_tab[last_col][-2:-1] = tmp_tab[last_col][-2:-1][0] + '*'
        #}}}

        # Вставка типа компонента в список и сборка в одну выходную таблицу {{{
        foot = tb.tabarray(records=[('','','','\\\\*'),('','','','\\\\')], names=(tmp_tab.dtype.names))

        if len(tmp_tab) > 0:
            if len(tmp_tab) > 1: # у нас больше 1 наименования компонентов
                # шапка и хвост для блока из одного типа элементов
                title = '\centering{'+component_des[key][1] + '}'
                head = tb.tabarray(records=[('',title,'','\\\\*'), ('','','','\\\\*')], names=(tmp_tab.dtype.names))

                # соберем в кучу шапку, тело и хвост
                if firstrun:
                    pe3_out = head.rowstack([tmp_tab,foot])
                    firstrun = False
                else:
                    pe3_out = pe3_out.rowstack([head,tmp_tab,foot])

            else: # наименование только одно
                # название вставляется прямо в строку
                tmp_tab['Item'][0] = component_des[key][0] + ' ' + tmp_tab['Item'][0]

                if firstrun:
                    pe3_out = tmp_tab.rowstack([foot])
                    firstrun = False
                else:
                    pe3_out = pe3_out.rowstack([tmp_tab,foot])
        #}}}

    return pe3_out
#}}}








# command line parser{{{
parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Usage text {{{
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
'''))#}}}

parser.add_argument('input_file', # {{{
        metavar='filename',
        type=file,
        help='path to file, generated by P-CAD')
        #}}}
parser.add_argument('-p','--pe3',#{{{
        metavar='FILENAME',
        type=str,
        default='pe3_table.tex',
        help='save pe3 to %(metavar)s (default: %(default)s)')
        #}}}
parser.add_argument('-s','--spec',#{{{
        metavar='FILENAME',
        type=str,
        default='spec_table.tex',
        help='save specification to %(metavar)s (default: %(default)s)')
        #}}}
parser.add_argument('-b','--bill',#{{{
        metavar='FILENAME',
        type=str,
        default='bill_table.tex',
        help='save bill list to %(metavar)s (default: %(default)s)')
        #}}}
parser.add_argument('-d','--delimiter', #{{{
        default='&',
        type=str,
        help='column separator in input file (default: %(default)s)')
#}}}

args = parser.parse_args()
#}}}


# cleaning input file and reading it to table{{{
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

# Hack! This line tell tabarray, that all columns contain string values
# Remove it after loading file
last_line = re.sub('[^&]',' ',raw_input_file[0])
out.write(last_line)
out.close()

# reading file into array 
x = tb.tabarray(SVfile = "cleaned_output.tmp",delimiter = '&',headerlines=1)
x = x[:-1] # remove hack-line
x = column_wide(x)
tmp_tab = x # create temporal array
os.remove("cleaned_output.tmp") # remove temporal file
#}}}







# now x contain final data. DO NOT touch them anymore!
x = prepare(x)

# анализ главного массива
indexing(x)

# build component list PE3
pe3_array = pe3(x)

# save table to file
save_to_file(args.pe3, pe3_array)









# автоматический aggregate годится только для генерации спецификации
# aggregate rows
#def refdes_agg(i):
#   return i[0]
#
#tmp_tab = x.aggregate(On=['Title','Type','SType','Value','Docum','Addit','Note','OrderCode'])
#
#print tmp_tab
#




