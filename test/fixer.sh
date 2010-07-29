#!/bin/sh
for i in `find -name "*.atr"`
do
	sed 's/\([0-9]*[.]\?[0-9]*\)\(k\?\)\( [51]%\)/\1 \2Ohm\3/' $i > ${i}__
done
