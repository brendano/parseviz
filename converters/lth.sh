perl -pe 's/\(ROOT/(/' | java -jar $(dirname $0)/pennconverter.jar
