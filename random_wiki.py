import urllib, urllib2, re, string, sys, time, datetime, random

# import tweepy (from local directory, if need be)
try:
	import tweepy
except ImportError:
	sys.path.append("../tweepy-1.4")
	import tweepy

# open creds file (private, uncommited storage of Bitly and Twitter credentials)
creds_file = open("creds")
creds = creds_file.read().split("\n")
bitly_un = creds[0]   # bitly username
bitly_key = creds[1]  # bitly API key
twitter_ck = creds[2] # twitter consumer key
twitter_cs = creds[3] # twitter consumer secret
twitter_at = creds[4] # twitter access token
twitter_as = creds[5] # twitter access token secret

# initialize twitter API using global creds, return API object
def tw_init():
	auth = tweepy.OAuthHandler(twitter_ck, twitter_cs)
	auth.set_access_token(twitter_at, twitter_as)

	api = tweepy.API(auth)
	return api

# list to define substrings which cannot end sentences
not_ends = ["mr", "mrs", "dr", "ms", "ph", "jr", "sr", "no", "esp", "pub", "br", "prof", \
"fr", "ii", "iii", "inc", "lt", "v", "bros", "bap", "var", "lit", "st", "ca", "and", \
"ave", "blvd", "ct", "ltd", "co", "eng", "jan", "feb", "aug", "sep", "oct", "nov", "dec"]
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

# get a snippet (first sentence, or portion thereof) from a body of text
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
		return None # caller should try again
	
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
	first_sentence = None
	shortened = ""
	while first_sentence == None:
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
			first_sentence = None # loop again
	
	return first_sentence + " " + shortened

# returns a good (somewhat random) time (float, in seconds) to wait before tweeting next
def get_wait_time():
	# as a base, wait between 1.5 and three hours
	t = random.randrange(1.5 * 60 * 60, 3 * 60 * 60)
	# add to this based on distance from 2:00pm (around which more tweets should happen)
	hour_offset = abs(14 - datetime.datetime.now().hour)
	t += random.randrange(hour_offset * 5, hour_offset * 10) # [0, 2] hours
	# go time
	return float(t)

# Entry point. The first argument from command line (optional) specifies how many seconds to wait before the first tweet.
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
			print "Waiting for %d hour(s), %d minutes before tweeting next...\n" % (wait_time / 60 / 60, (wait_time / 60) % 60)
			time.sleep(wait_time)
			now = datetime.datetime.now()
			
			# tweet
			tweet = get_random_page(120) # could have more chars, but this is nice
			api = tw_init() # init for every tweet, in case API times out
			print "[%s] Tweeting to account with name \"%s\":" % (now.strftime("%m/%d %H:%M"), api.me().name)
			print tweet
			api.update_status(tweet)
			
			# carry on
			wait_time = get_wait_time()
			when_set = time.time()
		
	except KeyboardInterrupt:
		# when the user quits, display how long it would have been (easy restarting)
		nxt = max(int(when_set + wait_time - time.time()), 0)
		print "\nWould have waited for %d hour(s), %d minutes before tweeting next (%d seconds).\n" % (nxt / 60 / 60, (nxt / 60) % 60, nxt)