#!/usr/bin/python
# -*- coding: cp1251 -*-

# TODO
# номиналы отбивать короткими пробелами от наименования физ. величины
# Сжимать позиционные обозначения по горизонтали, только если одно из них перевалило за 10
# Переименовать offset_parse() более адекватно
# вставить обработку исключений при подгрузке питоновых модулей, подсказывать, чего не хватает

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
# Как заполнять:
# 'key' : ['ед. число','мн. число','смещение','количество']
#
# Смещение и количество по умолчанию равны -1, они будут заполняться автоматически
# по мере анализа главной таблицы.
component_des = {	'C' : ['Конденсатор','Конденсаторы',-1,-1], \
					'R' : ['Резистор','Резисторы',-1,-1], \
					'D' : ['Микросхема','Микросхемы',-1,-1], \
					'DA': ['Микросхема','Микросхемы',-1,-1], \
					'DD': ['Микросхема','Микросхемы',-1,-1], \
					'VD': ['Диод','Диоды',-1,-1], \
					'XP': ['Вилка','Вилки',-1,-1], \
					'XS': ['Розетка','Розетки',-1,-1], \
					}
pos_names = sorted(component_des.keys())
#}}}

#}}}


def column_wide(narrow_tab): # функция для расширения столбцов {{{
# из-за недоработок колонки не могут расширяться динамически
# поэтому на придется заранее вставить в конец файла поля заведомо
# бОльшей ширины
# принимает обычную таблицу, возвращает "раздутую"

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
	wide_tab = wide_tab[:-1]

	return wide_tab
#}}}


def deleterow(input_tab,m): # функция удаления рядов из таблицы {{{

	if m == 0:
		return input_tab[1:]
	elif m == len(tmp_tab):
		return input_tab[:-1]
	else:
		aa = input_tab[:m]
		bb = input_tab[(m+1):]

	aa = aa.rowstack(bb)
	aa = column_wide(aa)

	return aa
#}}}


def save_to_file(filename,array): #{{{
	# taking basename from full path to file
	s = (re.sub('.*/|\.[^.]*$','',args.input_file.name) + '_table_pe3.tex')

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






def prepare(x): # cleaning table {{{

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
		if re.search('^[	]*$', x['Addit'][m]) == None: # если поле НЕ пустое
			x['Addit'][m] = ('<<' + x['Addit'][m] + '>>')
		m+=1
	#}}}

	# screaning latex special symbols{{{
	# this was moved here because & is input delimeter
	x.replace('&','\&',strict=False, cols=['RefDes', 'Title', 'Type', 'SType', 'Value', 'Docum', 'Addit', 'Note', 'OrderCode'])
	#}}}

	return x
#}}}


def indexing(x): # заполнение последних двух столбцов таблицы position_names{{{
	xlocal = x
	for key in pos_names:
		m = 0
		i = 0
		while m < len(xlocal):
			if xlocal['RefDes'][m] == key:
				i += 1
				if component_des[key][2] == -1:
					component_des[key][2] = m # смещение
			m += 1
		component_des[key][3] = i # количество

	#searching for unknown types of element
	m = 0
	fail = False
	for refdes in xlocal['RefDes']:
		known = False
		for key in pos_names:
			if refdes == key:
				known = True
		if not known:
			fail = True
			print '!!! Unknown element type:', xlocal['RefDes'][m] + str(xlocal['RefDesNum'][m])
		m += 1
	if fail:
		print '\nДальнейшая работа невозможна из-за наличия элементов неизвестного типа.'
		print 'Возможные причины: опечатка в RefDes при создании элемента для P-CAD,'
		print '                   либо, это - новый элемент, отсутствующий в базе.'
		print 'Если вышеуказанные элементы верны - добавьте их в базу \"component_des\"'
		print 'и прогоните скрипт заново.'
		quit()
#}}}


def pe3(x): # создание таблицы для перечня элементов{{{
	pe3_in = x 
	firstrun = True

	# merge columns
	m = 0 
	while m < len(pe3_in):
		pe3_in['Title'][m] = pe3_in['Type'][m] + \
				pe3_in['SType'][m] + ' ' + \
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
			prev = component_slice['RefDes'][m]	+	component_slice['Item'][m] +	component_slice['Note'][m]
			next = component_slice['RefDes'][m+1] + component_slice['Item'][m+1] +	component_slice['Note'][m+1]

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

	# запись полученной таблицы на диск
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
	# использование в регулярках '$' почему-то не прокатывает
	if re.search('^[	]*\r\n', line) == None: # if string non empty
		line = re.sub('"','',line) # delete all quotes
		line = re.sub('[ ]*&[ ]*','&',line) # delete unneeded spaces
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
# Don't forget to remove it after loading file
last_line = re.sub('[^&]',' ',raw_input_file[0])
out.write(last_line)
out.close()

# reading file into array 
x = tb.tabarray(SVfile = "cleaned_output.tmp",delimiter = '&',headerlines=1)
x = x[:-1] # remove hacked line
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
#	return i[0]
#
#tmp_tab = x.aggregate(On=['Title','Type','SType','Value','Docum','Addit','Note','OrderCode'])
#
#print tmp_tab
#




