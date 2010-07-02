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
x = tb.tabarray(SVfile = "test/_tmp0_last1.tex",delimiter = '&',headerlines=1)
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
		refdes_num.append(re.sub('[a-zA-Z]*','',x['RefDes'][m]))
		m += 1	
	# в RefDes запишем только буквы
	m = 0
	while m < len(x):
		x['RefDes'][m] = (re.sub('[0-9]*','',x['RefDes'][m]))
		m += 1
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
		x['Addit'][m] = ('<<' + x['Addit'][m] + '>>')
		# BUG: when string ends by 'or' - this end was gobbled
		# my be, do this with regexp string by string?
		# print x['Addit'][m]
		m+=1
	#}}}


	# cleaning data{{{
	x.replace('<< ','<<',strict=False,cols='Addit')
	x.replace(' >>','>>',strict=False,cols='Addit')
	x.replace('%',"\%",strict=False)
	#print x['Addit']
	#}}}

	return x
#}}}


def offset_parse(): # заполнение последних двух столбцов таблицы position_names{{{
	for key in pos_names:
		#print '---',key
		m = 0
		i = 0
		while m < len(x):
			if x['RefDes'][m] == key:
				i += 1
				if component_des[key][2] == -1:
					component_des[key][2] = m # смещение
			m += 1
		component_des[key][3] = i # количество
#}}}





def pe3():
	pe3_in = x # empty table
	pe3_out = x[:0] # empty table

	# merge columns
	m = 0 
	while m < len(pe3_in):
		pe3_in['Title'][m] = pe3_in['Type'][m]\
				+pe3_in['SType'][m]+ ' ' \
				+pe3_in['Value'][m]+ ' ' \
				+pe3_in['Docum'][m]+ ' ' \
				+pe3_in['Addit'][m]
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
	tmp_tab = pe3_in.deletecols(['Type', 'SType', 'Value', 'Docum', 'OrderCode'])
	pe3_in = tmp_tab

	







def old_pe3(): # aggregate strings together for component list (PE3)


	# now we have 'RefDes','Item','Sum','Note'
	# first and last lines process separatly
	m = 0
	flag_equal = 0
	prevRefDes = (m+1)
	nextRefDes = (m+2)
	lastRefDes = len(capacitors)

	# forming first line to tmp_tab
	tmp_tab = capacitors[:1] 
	tmp_tab['RefDes'][0] = 'C' + str(prevRefDes)
	tmp_tab['Sum'][0] = 1

	if len(capacitors) > 1:
		prev = capacitors['Item'][m] + capacitors['Note'][m]
		next = capacitors['Item'][m+1] + capacitors['Note'][m+1]
		while m < (len(capacitors)-1):
			if next == prev:
				prev = next
				next = capacitors['Item'][m+1] + capacitors['Note'][m+1]
				m += 1
			else: # сюда попадаем, если натыкаемся на незнакомую строку
				# добавим эту незнакомую строку в tmp_tab
				tmp_tab = tmp_tab.addrecords((capacitors['RefDes'][m], \
						capacitors['Item'][m], \
						capacitors['Sum'][m], \
						capacitors['Note'][m]))
				prev = next
				next = capacitors['Item'][m+1] + capacitors['Note'][m+1]
				nextRefDes = m
				print prevRefDes, nextRefDes, m
				print tmp_tab




				# обновим RefDes
				sum = nextRefDes - prevRefDes + 1
				if sum > 2:
					refdes = 'C' + str(prevRefDes) + '\dots ' + 'C' + str(nextRefDes)
				if sum == 2:
					refdes = 'C' + str(prevRefDes) + ',' + 'C' + str(nextRefDes)
				if sum == 1:
					refdes = 'C' + str(nextRefDes)
				# if we have more then one item in first line
				if sum > 0:
					tmp_tab['RefDes'][len(tmp_tab)-2] = refdes
					# запишем в предыдущую строку количество элементов
					tmp_tab['Sum'][len(tmp_tab)-2] = sum
				print tmp_tab

				prevRefDes = m + 1
				m += 1

		# действия по выходу из цикла
		print "out of cycle", prevRefDes, lastRefDes

		tmp_tab['Sum'][len(tmp_tab)-1] = (lastRefDes - prevRefDes + 1)
		tmp_tab['RefDes'][len(tmp_tab)-1] = ('C' + str(prevRefDes) + '\dots ' + 'C' + str(lastRefDes))
	return(tmp_tab)






# now x contain final data. DO NOT touch them anymore!
x = prepare(x)

# анализ главного массива
offset_parse()


# build component list PE3
pe3()








# теперь надо или снабдить шапкой типа \underline{Конденсаторы} или дописать "Конденсатор" по месту



#print tmp_tab
#print capacitors.dtype
#print capacitors[0]
















# автоматический aggregate годится только для генерации спецификации
# aggregate rows
#def refdes_agg(i):
#	return i[0]
#
#tmp_tab = x.aggregate(On=['Title','Type','SType','Value','Docum','Addit','Note','OrderCode'])
#
#print tmp_tab
#



x.saveSV('SampleData.csv', delimiter='&')

# sort by RefDes (badly works without leading zero)
# x.sort(order='RefDes')

# 			



#print(x)

