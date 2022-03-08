import datetime



def csv_read(csvpath):
	data = []
	header = ""
	with open(csvpath, 'r') as csvfile:
		header = csvfile.readline()[:-1].split(',')

		for line in csvfile:
			fields = line[:-1].split(',')
			data.append(dict(zip(header, fields)))

	return data, ','.join(header)


def fix_consecutives(data, index, avg_field, verbose):
	year, month, day = data[index]["Date"].split('-')
	today = datetime.datetime(int(year), int(month), int(day))
	expected_tomorrow = today + datetime.timedelta(days=1)

	year, month, day = data[index+1]["Date"].split('-')
	actual_tomorrow = datetime.datetime(int(year), int(month), int(day))

	if actual_tomorrow != expected_tomorrow:
		if verbose:
			print("Day missing: {}".format(str(expected_tomorrow)[:10]))
		#set all tomorrow values to Avg value of today
		fixed_tomorrow = dict.fromkeys(data[index], data[index][avg_field])
		#set tomorrow date to expected date
		#first 10 chars of str(datetime) contain YYYY-MM-DD
		fixed_tomorrow["Date"] = str(expected_tomorrow)[:10]
		data.insert(index+1, fixed_tomorrow)


def fix_zero(data, index, avg_field, verbose):
	if float(data[index][avg_field]) == 0.0:
		today_date = data[index]["Date"]
		if verbose:
			print("No data on day: {}".format(today_date))
		#set all today values to Avg value of yesterday
		fixed_today = dict.fromkeys(data[index-1], data[index-1][avg_field])
		#restore today date
		fixed_today["Date"] = today_date
		del data[index]
		data.insert(index, fixed_today)


def fix_missing_days(data, verbose):
	if not ("Weighted Price" in data[0]):
		avg_field = input("How is the Average field named?\n> ")
	else:
		avg_field = "Weighted Price"
	i=0
	while i+1 < len(data):
		fix_consecutives(data, i, avg_field, verbose)
		fix_zero(data, i, avg_field, verbose)
		i+=1


def csv_load(csvpath, verbose=False):
	if verbose:
		print("Loading from file {}".format(csvpath))
	data, header = csv_read(csvpath)
	data.reverse()
	if verbose:
		print("\nDone. Header is:\n{}\n".format(header))
	fix_missing_days(data, verbose)
	return data
