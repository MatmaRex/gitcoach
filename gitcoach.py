#!/usr/bin/env python

import sys, os, shutil, subprocess, pickle, numpy, signal, re

threshold = 0.8 # this is _entirely arbitrary_ 
data_file        = "/coaching_data"  
git_dir          = ""

git_get_current_changes = "git ls-files --full-name --modified" 

# Violating the "never cut and paste code" maxim, I know. FIXME 
def setup():

  get_git_dir = "git rev-parse --git-dir"

  try:
    global git_dir
    git_dir = subprocess.check_output( get_git_dir.split(), shell=False, universal_newlines=False)
  except subprocess.CalledProcessError as e:
    print ( "\nAre you sure we're in a Git repository here? I can't find the top-level directory.")
    exit ( e.returncode )

  if len(git_dir) == 0:
    print ("\nI can't find the git directory with \"git rev-parse --git-dir\", so I can't continue.\n" )
    exit (-1)

  os.chdir( git_dir[:-1] )

  return()

def coach():

  # OK, let's get the list of stuff we've currently modified and dare to compare.

  # FIXME - this next bit is ** guaranteed to break ** if you've got source files 
  # with whitespace in their names. I know: who does that, right? But it's still 
  # a bug.

  try: 
    git_current_changes = subprocess.check_output( git_get_current_changes.split(), shell=False, universal_newlines=True)
  except subprocess.CalledProcessError as e:
    print ( "\nAre you sure you're in a Git repository here? I can't find your list of current changes.")
    exit ( e.returncode )

  current_changeset = git_current_changes.strip().split("\n")

  # print ("Current changes: " + str(current_changeset) )

  if len(current_changeset) == 1 and current_changeset[0] == '' :
    print ("Nothing to do, exiting.") 
    exit(0)

  input_file = git_dir[:-1] + data_file
 
  try:
    input_stream = open(input_file, 'r')
  except IOError as e:
    print ("\nData file ( $REPO/.git/coaching_data ) either doesn't exist, or isn't accessible." + \
           "\nYou need to successfully run 'gitlearn' before you can run 'gitcoach' ." )
    exit ( -1 )
 
  try:
    names = pickle.load(input_stream)
    correlations = pickle.load(input_stream)
  except pickle.UnpicklingError as e:
    print ("\nI can't load the coaching_data file ( .git/coaching_data ). Try deleting it and" + \
           "\nre-running gitlearn to solve this problem.")
    exit(-1)

  total_files = len(names)

  suggestion_list = []
  suggestion_odds = []
  suggestion_data = [[]] # What nonsense. Consolidate these into one data structure later.

  for a_change in current_changeset:
    if a_change in names:
      index = names.index(a_change)
      for c in range(total_files):  # everything but the file you're examining.

        coincidence = correlations[index,c] / correlations[c,c]

        if coincidence > threshold and names[c] not in current_changeset:
          if names[c] not in suggestion_list:
            suggestion_list.append(names[c])
            suggestion_odds.append(coincidence)
            suggestion_data.append([a_change])
          elif suggestion_odds[suggestion_list.index(names[c])] < coincidence:
            suggestion_odds[suggestion_list.index(names[c])] = coincidence 
            suggestion_data[suggestion_list.index(names[c])].append(a_change)


          # An off by one error in here somewhere...

  if len(suggestion_list) == 0:
    print ("Nothing to see here, move along.")
    return()

  print ("\nGitcoach will tell you about the files that have, historically, been frequently committed\n" +\
         "to a Git repository at the same time as the files you've already modified. It presents this\n" +\
         "information in three columns: odds of coincident commits, file of interest, and the files\n" +\
         "you're working on that may be coincident.\n\n" +\
         "You might want to take a look at the following files:\n\n" )

  for x in range(len(suggestion_list)):
    print ( str(suggestion_odds[x] * 100) + "%\t" + str(suggestion_list[x]) + "\t\tSuggested by: " + str(suggestion_data[x] ) )

  return()

def finish():
  
  # clean up and exit - finish with a quote from either Yogi Berra or Casey Stengel.

  return()

def signal_handler(signal, frame):
  print ( "\nProcess interrupted. Goodbye.\n")
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

setup()
coach()
finish()

exit(0)
