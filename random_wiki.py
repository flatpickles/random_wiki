import urllib, urllib2, re, string, tweepy, sys, time

# usernames for services
bitly_un = "hazmattron"
twitter_un = "random_wiki"

# open creds file (private, uncommited storage of Bitly and Twitter credentials)
creds = open("creds")
both = creds.read().split("\n")
bitly_key = both[0]
twitter_pw = both[1]

# initialize tweepy
auth = tweepy.auth.BasicAuthHandler(twitter_un, twitter_pw)
twitter_api = tweepy.API(auth)

# list to define substrings which cannot end sentences
not_ends = ["mr", "mrs", "dr", "ms", "ph", "jr", "sr", "no", "b", "esp", "pub", "br", "prof", \
"fr", "c", "d", "b", "i", "ii", "iii", "inc", "lt", "v", "bros", "bap", "var", "lit", "st", \
"ave", "blvd", "ct", "ltd", "co", "eng", "jan", "feb", "aug", "sep", "oct", "nov", "dec", "ca", "and"]
not_ends.extend([l for l in string.ascii_lowercase])

# strips all substrings in txt surrounded by chars[0] and chars[1]
def strip_between(txt, chars):
	p = re.compile(chars[0]+'[^>]*?'+chars[1])
	return re.sub(p, '', txt)

# returns a shortened URL for url, using the Bitly API
def shorten(url):
	vals = {'uri': url, 'login': bitly_un, 'apiKey': bitly_key, 'format': 'txt'}
	enc = urllib.urlencode(vals)
	request_url = "http://api.bit.ly/v3/shorten?" + enc
	return request_url

# returns whether a string represents a number (even if number contains weird unicode)
def decode_digit(s):
	return re.sub('[^A-Za-z0-9]+', '', s).isdigit()

# get a first_sentence (first sentence, or portion thereof) from a body of text
def get_first_sentence(body, length):
	pgs = body.split("<p>")
	nohtml = strip_between(pgs[1].split("</p>")[0], ['<', '>'])
	nobrak = strip_between(nohtml, ['\[', '\]'])
	nodub = nobrak.replace("  ", " ")
	betweenp = nodub.replace(" .", ".").split(".")
	first_sentence = betweenp[0]
	
	# find the actual end of the sentence
	while True:
		if first_sentence.split(" ")[-1:][0].lower() in not_ends \
				or decode_digit(first_sentence.split(" ")[-1:][0]) \
				or first_sentence.split(".")[-1:][0].lower() in not_ends \
				or decode_digit(first_sentence.split(".")[-1:][0]) \
				or first_sentence.split("(")[-1:][0].lower() in not_ends \
				or decode_digit(first_sentence.split("(")[-1:][0]): # starting parens
			first_sentence += "." + betweenp[c]
		else: break
		
	# filter by some rules
	if len(first_sentence) == 0 or \
				len(first_sentence.split(" ")) < 4 or \
				"&" in first_sentence or \
				"\n" in first_sentence or \
				"refer to" in first_sentence or \
				"Wikify" in first_sentence or \
				"proper linking" in first_sentence or \
				"translated version" in first_sentence or \
				"Coordinate" in first_sentence or \
				"Glossary" in first_sentence or \
				":" in first_sentence or \
				"^" in first_sentence or \
				first_sentence[0] not in string.ascii_uppercase:
		return get_first_sentence(body, length)
	
	# otherwise, make presentable
	else:
		# remove questionmark (usually language advice)
		first_sentence = first_sentence.replace("?", "")
		
		if len(first_sentence) < length:
			if first_sentence[-1] != '.': return first_sentence + "."
			else: return first_sentence
		else:
			# remove last segment, add ...
			first_sentence = string.join(first_sentence[:(length-3)].split(" ")[:-1], " ")
			while first_sentence[-1] in string.punctuation:
				first_sentence = first_sentence[:-1]
			return first_sentence + "..."

# returns a string with the first snippit of a random wikipedia page and a link (provide characters desired)
def get_random_page(maxchars):
	first_sentence = ""
	shortened = ""
	while len(first_sentence) == 0:
		try:
			# get page and stuff
			opener = urllib2.build_opener()
			opener.addheaders = [('User-agent', 'Mozilla/5.0')]
			infile = opener.open('http://en.wikipedia.org/wiki/Special:Random')
			url = infile.geturl()
			shortened = urllib2.urlopen(shorten(url)).read().strip('\n')
			page = infile.read()
			first_sentence = get_first_sentence(page, maxchars - len(shortened))
		except Exception:
			first_sentence = "" # loop again
	
	return first_sentence + " " + shortened

# returns a good (somewhat random) time (float, in seconds) to wait before tweeting next
def get_wait_time():
	return 16.0

# entry point
if __name__ == "__main__":
	# determine how long to wait based on first argument (if present)
	wait_time = 0.0
	if len(sys.argv) > 1:
		wait_time = float(sys.argv[1])
	when_set = time.time()
	
	# until KeyboardInterrupt, tweet at intervals provided by get_wait_time
	try:
		while True:
			# sleep
			print "Waiting for %d seconds before tweeting next..." % wait_time
			time.sleep(wait_time)
			
			# tweet
			tweet = get_random_page(120)
			print "Tweeting: \"%s\"" % tweet
			
			# carry on
			wait_time = get_wait_time()
			when_set = time.time()
		
	except KeyboardInterrupt:
		print "\nYou killed random_wiki. Would have waited %d more seconds." % max(int(when_set + wait_time - time.time()), 0)