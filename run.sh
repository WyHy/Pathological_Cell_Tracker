while true
do
	python3 lbp_algo.py;
	status=$?
	if test $status -eq 0
	then
		echo "one job done"
	else
		echo "error occured"
		exit 1
	fi
done