#!/usr/bin/python
# -*- coding: cp1251 -*-


import string
import re
import tabular as tb
import numpy

# TODO:
# remove all double quotes, empty lines, wrong lines
# adding empty columns if needed
<<<<<<< HEAD
=======
# place Addit field in <<>>
# replace % by \%
>>>>>>> bash_parser
#
# ���������� �������� ����� �� ������ � ����������� �����������
# ������������ ������� int() ��� �������������� ������ � �����


right_order = ['RefDes', 'RefDesNum', 'Title', 'Type', 'SType', 'Value', 'Docum', 'Addit', 'Note', 'OrderCode']
right_num = len(right_order)


# ������� ��� ������ �� �������� ������� {{{
position_names = {	'C' : ('�����������','������������'), \
					'R' : ('��������','���������'), \
					'VD': ('����','�����'), \
					'XP': ('�����','�����'), \
					'XS': ('�������','�������'), \
					'D' : ('����������','����������'), \
					'DA': ('����������','����������'), \
					'DD': ('����������','����������'), \
					}
#}}}


# ��-�� ����������� ������� �� ����� ����������� �����������
# ������� �� �������� ������� �������� � ����� ����� ���� ��������
# ������� �����, ��������� ���� � tabarry � ������� ��������� ������

# reading file into array {{{
x = tb.tabarray(SVfile = '_tmp0_last1.tex',delimiter = '&',headerlines=1)
x = x[:-1] # remove last line
tmp_tab = x # create temporal array}}}

def prepare(x): # cleaning table {{{


	# split 'RefDes' column in two columns {{{
	refdes = []
	refdes_num = []
	# ������� ������� ����
	m = 0
	while m < len(x):
		refdes_num.append(re.sub('[a-zA-Z]*','',x['RefDes'][m]))
		m += 1	
	# � RefDes ������� ������ �����
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
#}}}




# now x contain final data. DO NOT touch them anymore!
prepare(x)





def pe3(): # aggregate strings together for component list (PE3){{{

	# catch strings with subsequent RefDes
	# first take capacitors
	my_list = []
	C = ["�����������", "������������", "capacitors"] 
	my_list.append(C)
	R = ["��������","���������","resistors"]
	my_list.append(R)

	m = 0
	n_begin = -1
	n_total = 0
	while m < len(x):
		RefDes = x['RefDes'][m]
		#print RefDes, RefDes[0:2]
		if RefDes[0:1] == 'C':
			if n_begin == -1:
				n_begin = m # first occurrence
			n_total += 1 # next occurrences increment end point
		m+=1

	#print n_begin
	#print n_total
	capacitors = x[right_order][n_begin:(n_begin+n_total)]
	#print capacitors

	m = 0 
	while m < len(capacitors):
		#print capacitors['Title'][m]
		capacitors['Title'][m] = capacitors['Type'][m]\
				+capacitors['SType'][m]+ ' ' \
				+capacitors['Value'][m]+ ' ' \
				+capacitors['Docum'][m]+ ' ' \
				+capacitors['Addit'][m]
		m+=1

	# rename 'Title' column
	capacitors.renamecol('Title','Item')

	# rename and clean 'Addit' columnt
	capacitors.renamecol('Addit','Sum')
	m = 0 
	while m < len(capacitors):
		capacitors['Sum'][m] = ''
		m += 1

	# remove unnecessary columns
	tmp_tab = capacitors.deletecols(['Type', 'SType', 'Value', 'Docum', 'OrderCode'])
	capacitors = tmp_tab


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
			else: # ���� ��������, ���� ���������� �� ���������� ������
				# ������� ��� ���������� ������ � tmp_tab
				tmp_tab = tmp_tab.addrecords((capacitors['RefDes'][m], \
						capacitors['Item'][m], \
						capacitors['Sum'][m], \
						capacitors['Note'][m]))
				prev = next
				next = capacitors['Item'][m+1] + capacitors['Note'][m+1]
				nextRefDes = m
				print prevRefDes, nextRefDes, m
				print tmp_tab




				# ������� RefDes
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
					# ������� � ���������� ������ ���������� ���������
					tmp_tab['Sum'][len(tmp_tab)-2] = sum
				print tmp_tab

				prevRefDes = m + 1
				m += 1

		# �������� �� ������ �� �����
		print "out of cycle", prevRefDes, lastRefDes

		tmp_tab['Sum'][len(tmp_tab)-1] = (lastRefDes - prevRefDes + 1)
		tmp_tab['RefDes'][len(tmp_tab)-1] = ('C' + str(prevRefDes) + '\dots ' + 'C' + str(lastRefDes))
	return(tmp_tab)
	#}}}


#pe3()








# ������ ���� ��� �������� ������ ���� \underline{������������} ��� �������� "�����������" �� �����



#print tmp_tab
#print capacitors.dtype
#print capacitors[0]
















# �������������� aggregate ������� ������ ��� ��������� ������������
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

