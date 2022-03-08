import os, datetime
import stalaGrapher

INFTY = 100.0 #10000% change is like infinite change, right?


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


def get_weekday(element):
	year, month, day = element["Date"].split('-')
	today = datetime.datetime(int(year), int(month), int(day))
	return today.weekday()


def periodic_analysis(data, num_days, granularity, percentile_radius, analysis_name):
	num_weeks = len(data)//float(num_days)
	if not (analysis_name[0] in data[0]):
		start_field = input("How is the "+analysis_name[0]+" field named?\n> ")
	else:
		start_field = analysis_name[0]
	if not (analysis_name[1] in data[0]):
		end_field = input("How is the "+analysis_name[1]+" field named?\n> ")
	else:
		end_field = analysis_name[1]

	#the intervals we want to keep track of:
	percent_intervals = []
	percent_intervals.append((-INFTY, -percentile_radius)) #leftmost
	percent_intervals.append((+percentile_radius, +INFTY)) #rightmost
	#and all the others in between:
	begin_int = -percentile_radius
	epsilon = granularity/10 #because floats suck
	while begin_int <= percentile_radius - granularity + epsilon:
		percent_intervals.append((begin_int, begin_int+granularity))
		begin_int += granularity

	#here is where we keep count of how many data points lie within each interval
	typical_day = dict.fromkeys(percent_intervals, 0)
	typical_week = [typical_day.copy() for day in range(num_days)]
	i=0
	while i+num_days-1 < len(data):
		this_week = [] #i-th element of this array is i-th day of the week
		for j in range(num_days):
			#our data set should start with a monday
			this_week.append(data[i+j])

		#record each day's end price relative to monday's end price
		for this_day in this_week:
			weekday = get_weekday(this_day)
			todays_change = float(this_day[end_field]) / float(this_week[0][start_field]) - 1.0
			for percent_interval in typical_week[weekday]:
				if percent_interval[0] <= todays_change <= percent_interval[1]:
					typical_week[weekday][percent_interval] += 1.0/num_weeks
					break

		i+=num_days

	return typical_week


if __name__ == "__main__":
	analysis = [["Open", "Close"], ["Open", "High"], ["Open", "Low"], ["Open", "Weighted Price"]]
	for an in analysis:
		for historyfile in os.listdir("CSVs"):
			if historyfile.endswith(".csv"):
				our_data = csv_load(os.path.join("CSVs", historyfile))
				percentile_radius = 0.20 #from -20% change to +20% change
				granularity = 0.01 #use intervals of +/-1% variation
				days_in_a_week = 7 #we are analyzing weekly behaviour, but we could choose any other period
				results = periodic_analysis(our_data, days_in_a_week, granularity, percentile_radius, an)

				#with open("results2.txt", 'w') as resultsfile2:
				#	resultsfile2.write(str(results))

				date_range = "From {} to {}".format(our_data[0]["Date"], our_data[-1]["Date"])
				plotpath = os.path.join("statsplots", an[1], an[1]+"_"+historyfile+".bmp")
				weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
				stalaGrapher.plot_analysis(results, an[1]+"_"+historyfile, date_range, percentile_radius, granularity, plotpath, weekdays)
