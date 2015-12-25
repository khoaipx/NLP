import os, sys, re, math, unicodedata, numpy as np, codecs, pickle

model_file_name = './model.pkl'

punct = [u'!', u',', u'.', u':', u';', u'?']  # TO DO : Add "..." etc
quotes = [u'"', u"'"]
brackets = [u'(', u')', u'[', u']', u'{', u'}']
mathsyms = [u'%', u'*', u'+', u'-', u'/', u'=', u'>', u'<']

def procress(sents):
	sents_ = []
	for sent in sents:
		sent_ = []
		for word in sent:
			# First, check if acronym or abbreviation, i.e. Z., Y.Z., X.Y.Z. etc.
			if re.search('(.\.)+\Z', word) and word.isupper(): 
				sent_.append(word) # Checked.
				continue 
			# Second, check if it is a date.
			# DD.MM.YY.
			if re.search('\A[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2}\.\Z', word):
				sent_.append(word) # Checked.
				continue
			# DD.MM.YYYY.
			if re.search('\A[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4}\.\Z', word):
				sent_.append(word) # Checked.
				continue
			# If not, separate out punctuation mark at end of word.
			for char in punct:
				rm = re.search('\\' + char + '+\Z', word)
				if rm:
					word = re.sub('\\' + char + '+\Z', '', word) + ' ' + char
					break
			sent_.extend(word.split())	
			
		sents_.append(sent_)

	f = open(model_file_name, 'rb')
	words_ = pickle.load(f) # Words with smoothed log probs.

	# Break word formation when encounter these characters (detached from any word).
	not_words_ = [u'!', u'"',  u'&', u"'", u'(', u')', u'*', u'+', u',', u'-', u'.',
                      u'/', u':', u';', u'=', u'>', u'?'] # u'%'
	f.close()	
	
	# f = codecs.open(output_file_name, mode = 'w', encoding = 'utf-8')
	ret = [] # returned result
	sents = [] # Tokenized sentences will be written here.

	for line in sents_:
		sent = []
		word = []

		for syl in line: # Consider each syllable in this line.

			# Check if syl is a punctuation mark or special character.
			if syl in not_words_: 
				if len(word) > 0:
					sent.append('[' + ' '.join(word) + ']') # Write current word to sentence surrounded by [].
					word = [] # Flush word.
				sent.append(syl) # Add the punct or special character (NOT as a token).
				continue
			word.append(syl)
			word1 = ' '.join(word) # Form new word by appending current syllable.

			# Check if the word exists in lexicon.
			if word1 in words_: 
				continue # Do not write anything, continue.

					
			# Otherwise, check if all syllables in current word are unknown, then keep going.
			# Reason: exploit the observation that unknown foreign words are usually clumped together as 				# single words. This improves P by 0.6 %, does not alter R, and improves F-ratio by 0.3 %.
			all_unk = 1
			for syl_ in word:
				if syl_ in words_:
					all_unk = 0
					continue 
			if all_unk:
				continue # i.e. clump together unknown words.

			# Check if it is a single unknown syllable.
			if len(word) == 1: # Keep it -> as it may be a bounded morpheme.
				continue # This test is not required, it is covered by the above test.

			# Check if first syllable is known, second unknown.
			# (Also, the first and second together do not make a valid word.)
			if len(word) == 2:
				sent.append('[' + word[0] + ']') # Then add 1st syllable as a word to the sentence.
				word = [word[1]] # Begin new word with 2nd syllable.

			# Check 1-lookahead with overlap ambiguity resolution.
			# Compare log prob(a, b_c) vs. log prob(a_b, c) if a, b_c, a_b, c exists in lexicon.
			# and write (a, b_c) or (a_b, c) accordingly.
			if len(word) > 2:
				word2 = ' '.join(word[:-2]) # (a)
				word3 = ' '.join(word[-2:]) # (b_c)
				word4 = ' '.join(word[:-1]) # (a_b)
				word5 = word[-1] # (c)
				if word3 not in words_ or word2 not in words_:
					sent.append('[' + word4 + ']')
					word = [word[-1]]
				elif word5 in words_ and word4 in words_:
					P1 = words_[word2] + words_[word3] # P(a, b_c)
					P2 = words_[word4] + words_[word5] # P(a_b, c)
					if P1 > P2:
						sent.append('[' + word2 + ']')
						word = word[-2:]
					else:
						sent.append('[' + word4 + ']')
						word = [word[-1]]
				else:
					# syl was an unknown word.
					sent.append('[' + word4 + ']')
					word = [word[-1]]
		# Last sentence.
		if len(word) > 0:
			sent.append('[' + ' '.join(word) + ']')
		if len(sent) > 0:
			sents.append(sent)
		# f.write(' '.join(sent) + '\n')
		ret.append(sent)
	return ret
	# f.close()

def set_model(_model_file_name):
	if not os.path.isfile(_model_file_name):
		print 'Model file "' + _model_file_name + '" does not exist. Retry with a valid file name.'
		exit(1)
	model_file_name = _model_file_name

def tokenize(input):
	return procress(input)

def tokenize_file(input_file_name):
	if not os.path.isfile(input_file_name):
		print 'Input text file "' + input_file_name + '" does not exist. Retry with a valid file name.'
		exit(1)
	f = codecs.open(input_file_name, mode = 'r', encoding = 'utf-8', errors = 'ignore')
	sents = []
	for line in f:
		sents.append(line.split()) # Split line on space to get syllables + etc.
	f.close()
	return token(sents)