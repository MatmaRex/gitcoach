#!/usr/bin/env python

import sys, os, shutil, subprocess, pickle, numpy, signal, re

# Using a few globals. Bad practice, I know.

starting_directory = ""
current_directory = ""
git_dir           = ""
temp_file         = "/.coaching_data" # leading slash matters
final_file        = "/coaching_data"  # in both these strings.

def get_commit_hashes():

# gitlearn passes through any command-line options to git rev-list unless
# it doesn't get any, in which case the default behavior is --all 

  list_all_commit_hashes = "git rev-list " 

  if len(sys.argv) < 2:
    list_all_commit_hashes += ( " --all" )
  else:
    for arg in sys.argv[1:]:
      list_all_commit_hashes += " " + arg

  try: 
    all_commit_hashes = subprocess.check_output( list_all_commit_hashes.split(), shell=False, universal_newlines=True)
  except subprocess.CalledProcessError as e:
    print ( "\nAre you sure we're in a Git repository here? I can't get any commit hashes.")
    exit ( e.returncode )
  
  return all_commit_hashes.strip().split()

def get_files_from_hash( commit_hash ):

  list_files_per_commit = "git show --pretty=format: --name-only " + commit_hash
  
  try:
    all_files_per_commit = subprocess.check_output( list_files_per_commit.split(), shell=False, universal_newlines=True)
  except subprocess.CalledProcessError as e:
    print ( "\nI couldn't get a list of modified files for this commit: " + commit_hash + "\n\nI don't know what to do here, so I'm exiting.")
    exit ( e.returncode )

  return all_files_per_commit.strip().split('\n')  


def learn():

  all_hashes = list()
  all_files = list()

  output_file = git_dir[:-1] + temp_file

  try: 
    output_stream = open(output_file, 'w')
  except IOError as e:
    print ("\nTemp file ( $REPO/.git/.coaching_data ) already exists, and I can't overwrite it." + \
           "\nThis shouldn't happen; you'll have to delete it manually and re-run gitlearn." )
    exit ( -1 )

  correlation = numpy.zeros(1)

  all_hashes = get_commit_hashes()

  for a_hash in all_hashes:
    files = get_files_from_hash(a_hash)  # future feature - treat "adding a file" as a correlation candidate (i.e. Makefiles)
   
    for f in files:
       if f not in all_files:

         all_files.append(f)
         k = all_files.index(f)
         s = len(all_files)

        # Grow the matrix and prepopulate.

         print ("Noting file " + str(f) )

         correlation = numpy.vstack([correlation,[0]*(s)])
         correlation = numpy.column_stack([correlation,[0]*(s+1)])
          
    for g in files:
      x = all_files.index(g)

      for h in files:                # FIXME: maybe don't walk the whole array twice, dummy.
        y = all_files.index(h)
        # print ( "correlating " + str(g) + " at [" + str(x) + "] with " + str(h) + " at [" + str(y) + "]" )
        correlation[x,y] += 1
    
  pickle.dump(all_files, output_stream)
  pickle.dump(correlation,output_stream)
  
  #print(correlation)

  output_stream.close()

  return()

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

def finish():
  
  # clean up and exit

  output_file = git_dir[:-1] + temp_file
  destination_file = git_dir[:-1] + final_file

  try:
    shutil.move(output_file, destination_file)
  except subprocess.CalledProcessError as e:
    print ( "\nIt looks like we can't overwrite the existing coaching_data file" + \
            "\nThis shouldn't happen; you'll have to delete it manually, then either copy" + \
            "\n .git/.coaching_data to .git/coaching_data or re-run gitlearn.")
    exit ( e.returncode )

  return()

def signal_handler(signal, frame):
  print ( "\nProcess interrupted. Goodbye.\n")
  sys.exit(0)
  
signal.signal(signal.SIGINT, signal_handler)

setup()
learn()
finish()



exit(0)

