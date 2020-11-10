#!/bin/sh

set -e

#find tests/ -name test.sh -execdir {} \;

for t in $(find tests/ -name test.sh );
do
	echo Running "$t"
	(
		cd $(dirname "$t")
		./test.sh
	)
done

echo -e "All \e[1;32mPASSED\e[0m!"
