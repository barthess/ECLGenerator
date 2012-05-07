#!/usr/bin/python
# -*- coding: utf8 -*-

import string
import re
import os
import tabular as tb
import sys

from globalvars import *
import utils

def removeplaceholders(tab):#{{{
    """ remove '*' placeholders from input table"""
    for i in tab.dtype.names:
        m = 0
        while m < len(tab):
            if tab[i][m] == '*':
                tab[i][m] = ''
            m+=1
    return tab
    #}}}
def removeunneededvalues(tab):#{{{
    """ Вычищает поле Value у тех элементов, которые не имеют номинала,
    например, микросхемы """

    def needkeep(st):
        re_list = [ '^C[0:9]*',
                    '^R[0:9]*',
                    '^R[0:9]*',
                    '^L[0:9]*',
                    '^RK[0:9]*',
                    '^RP[0:9]*',
                    '^ZQ[0:9]*']
        for i in re_list:
            if (re.match(i, st)) != None:
                return True
        return False

    m = 0
    while m < len(tab):
        if not needkeep(tab['Part'][m]):
            tab['Value'][m] = ''
        m+=1
    return tab
    #}}}
def quoteprofiteername(tab):#{{{
    """ Заключает название барыги в типографские кавычки """
    m = 0
    while m < len(tab):
        tab['VID'][m] = '<<' + tab['VID'][m] + '>>'
        m+=1
    return tab
    #}}}
def splitpartcolumn(tab):#{{{
    # split 'Part' column in two columns to simplify sorting
    parts = []
    parts_num = []
    # получим столбец цифр
    m = 0
    while m < len(tab):
        parts_num.append(int(re.sub('[a-zA-Z]*','',tab['Part'][m])))
        m += 1
    # в 'Part' запишем только буквы
    m = 0
    while m < len(tab):
        tab['Part'][m] = (re.sub('[0-9]*','',tab['Part'][m]))
        m += 1
    # добавим столбец номеров
    tmp_tab = tab.addcols([parts_num], names='PartN')
    return tmp_tab
    #}}}
def removeemptypartfield(tab):#{{{
    # remove rows with empty Part field
    m = 0
    deleted = False
    while m < len(tab):
        if tab['Part'][m] == '':

            log_msg = 'deleted: '
            for i in column_names:
                log_msg += str(tab[i][m])
            logfile.write(log_msg + '\n')

            tab = deleterow(tab,m)
            deleted = True
            m -= 1
        m += 1
    if deleted:
        print '*** Some elements deleted, because they have no Part field (see:',logfile.name,')'
    return tab
    #}}}
def removeunndedcolumns(tab):#{{{
    # remove columns with wrong name
    m = 0
    flag = 0
    for i in tab.dtype.names:
        while m < column_num:
            if column_names[m] == i: # raise flag if any match
                flag = 1
            m+=1
        if flag == 0:
            print '*** deleting column', i
            tmp_tab = tab.deletecols([i])
        m = 0
        flag = 0
    return tab
    #}}}
def stackcolumnsinrightorder(tab):#{{{
    # stack columns 1 by 1 in right order
    tmp_tab = tab[['Part']] # save to tmp_tab first column
    m = 1
    while m < column_num:
        z = tmp_tab.colstack(tab[[column_names[m]]])
        tmp_tab = z
        m+=1
    return z
    #}}}
def processvalues(tab): #{{{
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

    def pseudo_translate(st):#"перевод" значений на русский язык {{{
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
        #}}}
    def valueclean(oldstring, *args): # вспомогательная функция {{{
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
                # заэкранируем %
                s1 = re.sub('%','\\\\%,',s1)
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

	# снабдим процентаж знаком плюс-минус (\textpm)
	newstring = re.sub('([0-9]*[,]*[0-9]*",\\\\%)',' {\\\\textpm}",\\1',newstring)
        # вычистим из конца пробелы, которые остались от старой строки
        newstring = re.sub('[	]*$','',newstring)
	return newstring
    #}}}

    # process Value column
    m = 0
    while m < len(tab):
        s = tab['Value'][m]
        part = tab['Part'][m]

        # логика выбора нужных регулярок в зависимости от типа элемента
        if part ==    'C':
            s = valueclean(s, capacitance, tolerance, voltage)
        elif part ==  'L':
            s = valueclean(s, inductance, tolerance, current)
        elif (part == 'R') | (part == 'RP'):
            s = valueclean(s, resistance, tolerance, power)
        elif (part == 'RK'):
            s = valueclean(s, current, power)
        elif part == 'ZQ':
            s = valueclean(s, frequency, tolerance)
        else: # обработчик лажи
            unknown_element = True
            for i in pos_names:
                if part == i:
                    unknown_element = False
            if unknown_element:
                # аварийное завершение, скрипт не знает такого элемента
                print 'ERROR!. I don\'t know the element type:',part
                print 'Add it manually.'
                quit()

        # Дополнительные вычистки
        # тут же можно поудалять лишних пробелов
        s = re.sub('[ ]*",[ ]*','",',s)
        s = re.sub('^[ ]*|[ ]*$','',s)
        s = re.sub('[ ]+',' ',s)

        # а так же случайно попавшие двойные последовательности вроде ",",
        s = re.sub('",+','",',s)

        # вписываем обработанную строку обратно в таблицу
        tab['Value'][m] = s

        m += 1

    return tab
#}}}
def mboxing(tab, *columns): #{{{
    """ Заключение нужных ячеек в \mbox{}.

    Принимает имя таблицы и имена колонок, которые надо заключить в mbox.

    Возвращает обработанную таблицу.
    """
    if len(columns) == 0:
        return(tab)

    m = 0
    i = ''
    while m < len(tab):
        for i in (columns):
            if not re.match('^[ ]*$', tab[i][m]): # if not empty string
                tab[i][m] = '\mbox{' + tab[i][m] + '}'
        m += 1
    return(tab)
#}}}


def prepare(tab): # {{{
    """ Функция предварительной очистки и подготовки.
    Удаляет
    """

    tab = removeplaceholders(tab)
    tab = removeunneededvalues(tab)
    tab = quoteprofiteername(tab)
    tab = splitpartcolumn(tab)
    tab = removeemptypartfield(tab)
    tab = removeunndedcolumns(tab)
    tab = stackcolumnsinrightorder(tab)

    # sort by part name
    tab.sort(order=['Part'])

    # add russian LaTeX quotas to column 'Mfg Name'
    m = 0
    while m < len(tab):
        if re.search('^[    ]*$', tab['Mfg Name'][m]) == None: # если поле НЕ пустое
            tab['Mfg Name'][m] = ('<<' + tab['Mfg Name'][m] + '>>')
        m+=1

    tab = processvalues(tab)

    # enclose in mbox
    tab = mboxing(tab, 'Part Num','Value', 'VID', 'Vendor Part Num', 'Mfg Name', 'Package', 'Country of Origin')
    # print tab.dtype.names
    # exit()

    return tab
#}}}




