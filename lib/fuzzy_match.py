

def fuzzyMatch(s, valid):
	"""
		matches the s in a fuzzy way against the keys of the dictionary valid,
		the corresponding value is returned
	"""
	
	s = s.strip()
	fuzzy_matches = []
	
	# try to match s to a valid key
	for key,value in valid.items():
		# in case of an exact match, use the token
		if s == key:
			return value
		# in case of a fuzzy match, add key,value to the fuzzy match list
		fuzzy = lambda s: s.lower().replace(' ','')
		if fuzzy(key).startswith( fuzzy(s) ):
			fuzzy_matches.append((key,value))
	else:
		# if there was no exact match, see if we have at least fuzzy matches
		if len(fuzzy_matches) == 0:
			raise ValueError("no candidates")
		elif len(fuzzy_matches) >= 2:
			candidates = ", ".join(sorted(key for key,value in fuzzy_matches))
			raise ValueError("too many candidates: %s" % candidates)
		else:
			# if there is only one fuzzy match, return the corresponding value
			return fuzzy_matches[0][1]
