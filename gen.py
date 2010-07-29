#!/usr/bin/python
# -*- coding: cp1251 -*-

# TODO:

# ������� ��������� ��� �������� ��������� ����� ������ ������ �����������:
# kOhm, MOhm, pF ��� ������� �������� ������������ � P-CAD ������ � ���������
# �������: �������, �������, ������������ ������������ ������������� ��������:
# uF, V

# ������� ����������� ����������� �� �����������, ������ ���� ���� �� ���
# ���������� �� 10

# �������� ��������� ���������� ��� ��������� ��������� �������, ������������,
# ���� �� �������

# ������� pe3 �������� ������, ����� ������� ��� �������� ������������. ����
# �� ��� �������� ��������� � ����� �������� ������, ��� ������� ��� � ����
# (���������?) ������� �������


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

# ��������� ��������� {{{
# ������ �������� ����� ��� ����������� ������ �������
column_strut = ' ' * 1024
#}}}

# ��������� ������ ������� {{{
# ������ ������ �������� ���������� �������� �������, ��� �� ������� P-CAD
# ��� ������ ���� � ��� �������, ��� ������ ���������� �������
column_names = ['RefDes', 'RefDesNum', 'Title', 'Type', 'SType', 'Value', 'Docum', 'Addit', 'Note', 'OrderCode']
column_num = len(column_names)
#}}}

# ������� ��� ������ �� �������� ������� {{{
# 
# ��� �������� ��� ��������� ��� ��������. ���� ��������� ����������� -
# ������ ������� ���������� � ��������� ������������ �������� ����
# ����������� �������
#
# ��� ���������:
# 'key' : ['��. �����','��. �����','��������','����������']
#
# �������� � ���������� �� ��������� ����� -1, ��� ����� �����������
# �� ����� ������� ������� �������.
component_des = {   'C' : ['�����������','������������',-1,-1], \
                    'E' : ['���������','���������',-1,-1], \
                    'R' : ['��������','���������',-1,-1], \
                    'D' : ['����������','����������',-1,-1], \
                    'DA': ['����������','����������',-1,-1], \
                    'DD': ['����������','����������',-1,-1], \
                    'L' : ['��������','��������',-1,-1], \
                    'RK': ['�������������','��������������',-1,-1], \
                    'RP': ['�������� ������������','��������� ������������',-1,-1], \
                    'VD': ['����','�����',-1,-1], \
                    'XP': ['�����','�����',-1,-1], \
                    'XS': ['�������','�������',-1,-1], \
                    'Z' : ['������ ��������������','������� ��������������',-1,-1], \
                    'ZQ': ['��������� ���������','���������� ���������',-1,-1], \
                    }
# �������� �����������, ������ ��� ��������� ������� �������� 
# �������� � ��������� �������
pos_names = sorted(component_des.keys())
#}}}

#}}}


def column_wide(narrow_tab): #{{{
    """ ������� ��� ���������� ��������

    ��������� ������� �������, ���������� "��������"

    ��-�� ����������� ������ tabular ������� �� ����� ����������� �����������,
    ������� �� �������� ������� �������� � ����� ����� ���� ��������
    ������� ������.
    """
    # crate fake row
    first_row = narrow_tab[:1] # ������� ������ ��� ��� ����������� ���� �������
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
    """ ������� �������� ����� �� �������.

    ��������� ������� ������� � ����� ����, ������� ���� �������.

    ���������� ������� ��� ���������� ����.

    ������� �������� ������, ���� ����� �������� 2 �����,
    � ����� ������� �� ������.
    """
    if m == 0:
        return input_tab[1:]
    elif m == len(tmp_tab):
        return input_tab[:-1]
    else:
        aa = input_tab[:m]
        bb = input_tab[(m+1):]

    aa = aa.rowstack(bb)
    aa = column_wide(aa) # ������� �������

    return aa
#}}}


def save_to_file(filename, array): #{{{
    """ ������� ���������� ������� � ����.

    ��������� ��� ��������� ����� � �������, ������� ���� ���������

    �� ���������� ������

    ������� ����������, ���������� � tabular, ��������� �������� ������� �
    ������ ������ ��������� �����. ��� ��� �� ��������. �������� ������� ���
    ����� ���������� ����� �� ����.
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
    """ �������� ���� Value � ����������� ����.

    ��������� ������ � ��� ��������, ����. C, L, R.
    ��� �������� ����� ��� ������ ���������� ��������.

    ���������� ������������ ������.
    """

    # ���������� ��������� ��� ������ ���������{{{
    tolerance =     re.compile('[0-9]*[.,]*[0-9]*[ ]*\\\\%')

    capacitance =   re.compile('[0-9]*[.,]*[0-9]*[ ]*[umnp]?F')
    current =       re.compile('[0-9]*[.,]*[0-9]*[ ]*[num]?A')
    frequency =     re.compile('[0-9]*[.,]*[0-9]*[ ]*[kMG]?Hz')
    inductance =    re.compile('[0-9]*[.,]*[0-9]*[ ]*[unm]?H')
    power =         re.compile('[0-9]*[.,]*[0-9]*[ ]*[umk]?W')
    resistance =    re.compile('[0-9]*[.,]*[0-9]*[ ]*[mkM]?Ohm')
    voltage =       re.compile('[0-9]*[.,]*[0-9]*[ ]*[mkM]?V')
    #}}}

    def clean(oldstring, *args): # ��������������� ������� {{{ 
        """ ��������� ������ �����������.

        ��������� ������, ������� ���� ���������� � ����������������
        ���������, �������� ���� ������������. ������� ��������� �����
        �������� - �� ���������� ������� ���������� �������� ��������� �
        �������� ������. �����, ��������������� ���������� ������������ ��
        ������� ������ � �� ���� ������ ������������ �������� ������.  �������
        ������� ������ (��, ��� �� ������ �� � ���� ���������) ������������ �
        �����.

        ���������� ������������ ������.
        """
        newstring = ''
	s1 = ''
        for regexp in (args):
            t1 = regexp.findall(oldstring)
            if len(t1) > 0:
                # ������� ������ �������
                s1 = re.sub('([0-9]*)([.,]*)([0-9]*)([ ]*)([a-zA-Z\\\\%]*)','\\1\\2\\3",\\5',t1[0])
                # �������� ����� �� �������
                s1 = re.sub('([0-9]*)[.,]([0-9]*",)','\\1,\\2',s1)
                # �������� ������� ����
                s1 = re.sub('^,','0,',s1)
                # FIXME: ��� ������� ����� ��������� �� �������
                newstring += (s1 + ' ')

            # ������ newstring �������� ��� ������ ��� ��������� � ������ �������
            # ���� ������� �� �� �������� ������
            oldstring = regexp.sub('',oldstring)

        # ������� ������ ������ ��������� � ����� �����
        # TODO: ���� �������� ���-�� ����� �������� ������ �������
        #if re.search('[^     ]*',oldstring)
        newstring = newstring + oldstring
	# ������� ��������� ������ ����-����� (\textpm)
	newstring = re.sub('([0-9]*[,]*[0-9]*",\\\\%)',' {\\\\textpm}",\\1',newstring)
        # �������� �� ����� �������, ������� �������� �� ������ ������
        newstring = re.sub('[	]*$','',newstring)
	return newstring
    #}}}

    # ������ ������ ������ ��������� � ����������� �� ���� �������� {{{
    if refdes ==    'C':
        s = clean(s, capacitance, tolerance, voltage)
    elif refdes ==  'L':
        s = clean(s, inductance, tolerance, current)
    elif (refdes == 'R') | (refdes == 'RK') | (refdes == 'RP'):
        s = clean(s, resistance, tolerance, power)
        # FIXME: ������������� ����� ���������� \textohm
        #s = re.sub('Ohm','{\\\\textohm}',s)
    elif refdes == 'ZQ':
        s = clean(s, frequency, tolerance)
    else: # ���������� ����
        unknown_element = True
        for i in pos_names:
            if refdes == i:
                unknown_element = False
        if unknown_element:
            # ��������� ����������, ������ �� ����� ������ ��������
            print 'Something goes wrong. I don\'t know element type:',refdes
            quit()
    #}}}

    # �������������� ��������{{{
    # ��� �� ����� ��������� ������ ��������
    s = re.sub('[ ]*",[ ]*','",',s)
    s = re.sub('^[ ]*|[ ]*$','',s)
    s = re.sub('[ ]+',' ',s)

    # � ��� �� �������� �������� ������� ������������������ ����� ",",
    s = re.sub('",+','",',s)
    #}}}

    return s
#}}}


def prepare(x): # {{{
    """ ������� ��������������� ������� � ����������.

    """
    # split 'RefDes' column in two columns {{{
    refdes = []
    refdes_num = []
    # ������� ������� ����
    m = 0
    while m < len(x):
        refdes_num.append(int(re.sub('[a-zA-Z]*','',x['RefDes'][m])))
        m += 1
    # � RefDes ������� ������ �����
    m = 0
    while m < len(x):
        x['RefDes'][m] = (re.sub('[0-9]*','',x['RefDes'][m]))
        m += 1
    # ������� ������� �������
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
        if re.search('^[    ]*$', x['Addit'][m]) == None: # ���� ���� �� ������
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
    """ ������� ������ ����� � ���������� ������ ����.

    ����������, ���������� ��������� ���� �������� ������� position_names
    """
    for key in pos_names:
        m = 0
        i = 0
        while m < len(array):
            if array['RefDes'][m] == key:
                i += 1
                if component_des[key][2] == -1:
                    component_des[key][2] = m # ��������
            m += 1
        component_des[key][3] = i # ����������

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
    """ ���������� ������ ����� � \mbox{}.

    ��������� ��� ������� � ����� �������, ������� ���� ��������� � mbox.

    ���������� ������������ �������.
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
    """ �������� ������� ��� ������� ���������.

    ����, � �� �������!
    ���� ����������, ����������, ��� ����� �� ������� �������
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

    for key in pos_names: # ���������� ����� {{{
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
                else: # ���� ��������, ���� ���������� �� ���������� ������
                    # ������� ��� ���������� ������ � tmp_tab
                    tmp_tab = tmp_tab.addrecords((component_slice['RefDes'][m+1], \
                            component_slice['RefDesNum'][m+1] - 1, \
                            component_slice['Item'][m+1], \
                            component_slice['Sum'][m+1], \
                            component_slice['Note'][m+1]))
                    # ������� RefDesNum �� ���� ������� �����, ����� �� �������� ��������
                    tmp_tab['RefDesNum'][len(tmp_tab) - 2] = tmp_tab['RefDesNum'][len(tmp_tab) - 1]
                    # take next row
                    prev = next
                    next = component_slice['RefDes'][m+2] + component_slice['Item'][m+2] + component_slice['Note'][m+2]
                m += 1

            # �� ������ �� ����� �������� ������������� ��� ����� ��������
            tmp_tab['RefDesNum'][len(tmp_tab) - 1] = component_slice['RefDesNum'][m+1] - 1

            # ����������� ���������� ��������� ���
            # ���� ���������� �����, ���� ��������� RefDesNUm
            if next == prev:
                tmp_tab['RefDesNum'][len(tmp_tab)-1] = component_slice['RefDesNum'][m+1]
            else:
                tmp_tab = tmp_tab.addrecords((component_slice['RefDes'][m+1], \
                        component_slice['RefDesNum'][m+1], \
                        component_slice['Item'][m+1], \
                        component_slice['Sum'][m+1], \
                        component_slice['Note'][m+1]))
        #}}}

        # ���������� ���� RefDes {{{
        if len(tmp_tab) > 0:

            def scale(str):
                str = '\scalebox{0.75}[1]{' + str + '}'
                return str

            m = 0
            while m < len(tmp_tab):
                sum = 0
                if m == 0: # ���� �� � ������ ����
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

        # ������� ���� ���������� � ������ � ������ � ���� �������� ������� {{{
        foot = tb.tabarray(records=[('','','','\\\\*'),('','','','\\\\')], names=(tmp_tab.dtype.names))

        if len(tmp_tab) > 0:
            if len(tmp_tab) > 1: # � ��� ������ 1 ������������ �����������
                # ����� � ����� ��� ����� �� ������ ���� ���������
                title = '\centering{'+component_des[key][1] + '}'
                head = tb.tabarray(records=[('',title,'','\\\\*'), ('','','','\\\\*')], names=(tmp_tab.dtype.names))

                # ������� � ���� �����, ���� � �����
                if firstrun:
                    pe3_out = head.rowstack([tmp_tab,foot])
                    firstrun = False
                else:
                    pe3_out = pe3_out.rowstack([head,tmp_tab,foot])

            else: # ������������ ������ ����
                # �������� ����������� ����� � ������
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
    # ������������� � ���������� '$' ��� ������-�� �� �����������
    # \r\n - �������� ����� ������, \n - ���������, ���, �� ������ ������
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

# ������ �������� �������
indexing(x)

# build component list PE3
pe3_array = pe3(x)

# save table to file
save_to_file(args.pe3, pe3_array)









# �������������� aggregate ������� ������ ��� ��������� ������������
# aggregate rows
#def refdes_agg(i):
#   return i[0]
#
#tmp_tab = x.aggregate(On=['Title','Type','SType','Value','Docum','Addit','Note','OrderCode'])
#
#print tmp_tab
#




