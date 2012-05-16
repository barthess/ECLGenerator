#!/bin/bash
# Script for converting from html table to tab separated table

cat $1 | sed 's/<\/b><\/td><td><b>/\t/g' | sed 's/<\/td><td>/\t/g' | sed 's/<tr><td>//' | sed 's/<\/td><\/tr>//' | sed 's/^<b>//' | sed 's/<\/b>$//' | sed '$d' | sed '1,3d'
