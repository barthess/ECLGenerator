#!/usr/bin/python
# -*- coding: cp1251 -*-


import string
import re
import tabular as tb
import numpy
from operator import itemgetter # for sort() and sorted()


# TODO:
# remove all double quotes, empty lines, wrong lines
# adding empty columns if needed
#
# Регуляркой отделить буквы от номера в позиционном обозначении
# использовать функцию int() для преобразования строки в число



# preparing some data structures {{{


# данный список содержит названия колонок, как их генерит P-CAD в нужном порядке
right_order = ['RefDes', 'RefDesNum', 'Title', 'Type', 'SType', 'Value', 'Docum', 'Addit', 'Note', 'OrderCode']
right_num = len(right_order)


# словарь для поиска по готовому массиву 
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


# из-за недоработок колонки не могут расширяться динамически
# поэтому на придется заранее вставить в конец файла поля заведомо
# бОльшей шириы, прочитать файл в tabarry и удалить последнюю строку

# reading file into array {{{
x = tb.tabarray(SVfile = "test/_tmp0_mid2.tex",delimiter = '&',headerlines=1)
x = x[:-1] # remove last line
tmp_tab = x # create temporal array}}}


def usage(): #{{{
	print """ stub """
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


	# remove wrong columns{{{
	m = 0 
	flag = 0
	for i in x.dtype.names: 
		while m < right_num: 
			if right_order[m] == i: # raise flag if any match
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
	for i in right_order:
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
	while m < right_num: 
		z = tmp_tab.colstack(x[[right_order[m]]])
		tmp_tab = z
		m+=1
	x = z # now x contain columns in right order 
	#}}}


	# add russian LaTeX quotas to column 'Addit'{{{
	m = 0
	while m < len(x):
		if re.search('^[	]*$', x['Addit'][m]) == None:
			x['Addit'][m] = ('<<' + x['Addit'][m] + '>>')
		# BUG: when string ends by 'or' - this end was gobbled
		# my be, do this with regexp string by string?
		# print x['Addit'][m]
		m+=1
	#}}}


	# cleaning data{{{
	x.replace('<< ','<<',strict=False,cols='Addit')
	x.replace(' >>','>>',strict=False,cols='Addit')
	x.replace('%',"\%",strict=False,cols=('Title', 'Type', 'SType', 'Value', 'Docum', 'Addit', 'Note', 'OrderCode'))
	#}}}
	return x

#}}}


def offset_parse(x): # заполнение последних двух столбцов таблицы position_names{{{
	for key in pos_names:
		m = 0
		i = 0
		while m < len(x):
			if x['RefDes'][m] == key:
				i += 1
				if component_des[key][2] == -1:
					component_des[key][2] = m # смещение
			m += 1
		component_des[key][3] = i # количество
	return x
#}}}


def pe3(): # создание таблицы для перечня элементов{{{
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
		# Возможно понадобится что-то вроде \scalebox{0.8}[1]{R133\dots R145} или \resizebox

		if len(tmp_tab) > 0:
			m = 0
			while m < len(tmp_tab):
				sum = 0
				if m == 0: # если мы в первом ряду
					sum = int(tmp_tab['RefDesNum'][m])
					if sum > 2:
						refdes = str(key) + '1' + '\mbox{.\kern -0.3mm .\kern -0.3mm .}' + str(key) + str(tmp_tab['RefDesNum'][m])
					if sum == 2:
						refdes = str(key) + '1' + ', ' + str(key) + str(tmp_tab['RefDesNum'][m])
					if sum == 1:
						refdes = str(key) + str(tmp_tab['RefDesNum'][m])

				else:
					sum = int(tmp_tab['RefDesNum'][m]) - int(tmp_tab['RefDesNum'][m-1])
					if sum > 2:
						refdes = str(key) + str(tmp_tab['RefDesNum'][m-1] + 1) + '\mbox{.\kern -0.3mm .\kern -0.3mm .}' \
								+ str(key) + str(tmp_tab['RefDesNum'][m])
					if sum == 2:
						refdes = str(key) + str(tmp_tab['RefDesNum'][m-1] + 1) + ', ' + str(key) + str(tmp_tab['RefDesNum'][m])
					if sum == 1:
						refdes = str(key) + str(tmp_tab['RefDesNum'][m])

				# if we have more then one item in first line
				if sum > 0:
					tmp_tab['RefDes'][m] = refdes
					tmp_tab['Sum'][m] = sum
				m += 1
		#}}}
		
		tmp_tab = tmp_tab.deletecols('RefDesNum') # remove unneeded column

		# add LaTeX new line symbol {{{
		m = 0
		last_col = str(tmp_tab.dtype.names[-1:])[2:-3]
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

		if len(tmp_tab) > 1: # у нас больше 1 наименования компонентов
			# шапка и хвост для блока из одного типа элементов
			title = '\centering\underline{'+component_des[key][1] + '}'
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
	pe3_out.saveSV('pe3.tmp', delimiter='&')
#}}}


def wrappe3():
	with open('pe3.tmp','r') as f:
		data = f.readlines()
		f.close()
	
	# тут вставить исключение, если не найден файл
	# и вместо файла использовать готовый набор строк
	with open('preamble_pe3.tex','r') as f:
		preamble = f.read()
		f.close()
	
	with open('out.tex','w') as f:
		f.write(preamble)
		m = 1 # чтобы пропустить первую строку
		while m < len(data):
			f.write(data[m])
			m += 1
		f.write('\end{ESKDcomponentList}\end{document}')
		f.close











# now x contain final data. DO NOT touch them anymore!
x = prepare(x)


# анализ главного массива
x = offset_parse(x)


# build component list PE3
pe3()


wrappe3()










# автоматический aggregate годится только для генерации спецификации
# aggregate rows
#def refdes_agg(i):
#	return i[0]
#
#tmp_tab = x.aggregate(On=['Title','Type','SType','Value','Docum','Addit','Note','OrderCode'])
#
#print tmp_tab
#




