#!/bin/sh
# Usage: 
# merge filename_without_extension

# TODO
# ������ ������ �������� ������ �������, � ������ ����������� � ���������� �������


DOCUMENT=$1
n=0 # cycle counter
MATCH=0 # matching flag

# column names in right order
colname[1]="RefDes"
colname[2]="Title"
colname[3]="Type"
colname[4]="SType"
colname[5]="Value"
colname[6]="Docum"
colname[7]="Addit"
colname[8]="Note"
colname[9]="OrderCode"


# delete head from table
sed -e 's/"//g' $DOCUMENT.atr |  sed -e '2d' > _tmp$n.tex




# analize table head
q=1
for i in `sed -n '1p' _tmp$n.tex | sed -e 's/\&/ /g' | sed -e 's/"//g'`
do
	MATCH=0
	j=1
	while (( $j <= 9 ))
	do
		# echo "$i $j $q"
		if [[ $i == ${colname[$j]} ]]
		then
			MATCH=1 # ������ ������� ������
		else
			echo "------- $i $j $q"
		fi
		((j++))
	done

	if [[ $MATCH == 0 ]]
	then
		sed -e "s/[^&]*\&//$q" _tmp$n.tex > _tmp$((n+1)).tex
		((n++))
	fi
	((q++))
done







# ������� ������� ��� ��������� �������


# ������ �������� - ����� ������� ��� ��������, ��������� - ����� ������
# sed -e "s/[^&]*\&//$NUM"



# ������ ������� ������ � ������ �������
# awk ' BEGIN{FS="&";OFS="&"} { tmp=""; tmp=$1; $1=$2; $2=tmp; print}'







# clean 
# rm _tmp*.*

