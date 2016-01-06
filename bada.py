'''
bada is stupid a command line tool
for working with aws lambda and making
the dev workflow better 

ie tests
'''
import boto3
import json
import os
import zipfile
import StringIO
import sys

DOTFILE = '.bada'
DEFAULT_JOB = '''

def handler(event, context):
  pass

'''

client = boto3.client('lambda')
iam_client = boto3.client('iam')

def zipdir(path, ziph):
  for root, dirs, files in os.walk(path):
    for file in files:
      ziph.write(os.path.join(root, file))

def zip_full_directory():
  print 'zipping up folder contents...'
  tmp_space = StringIO.StringIO()
  with zipfile.ZipFile(tmp_space, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    zipdir('.', zf)
  return tmp_space.getvalue()

def make_new_lambda_function():
  print '''Looks like a dotfile doesn't exist for this folder, let's instantiate a job...'''

  # get roles
  role_data = iam_client.list_roles()
  available_roles = role_data['Roles']

  job_name = raw_input("Lambda Job Name: ")

  i = 1
  for role in available_roles:
    print "(%s) %s %s" % (i, role['RoleName'], role['Arn'])
    i += 1

  picked_role = int(raw_input("Pick IAM Role: "))
  description = raw_input("Enter Description: ")
  timeout = raw_input("Timeout (default = 3s): ")
  create_job = raw_input("Would you like to create a new job file (Y/N)?: ")

  try:
    timeout = int(timeout)
  except:
    timeout = 3

  # create the job if the creator wants to
  if create_job in ('Y', 'y'):
    print "Creating empty job file.."
    with open(job_name + '.py', 'w') as fh:
      fh.write(DEFAULT_JOB)

  # now zip up the contents of this folder
  print 'zipping up folder contents...'
  tmp_space = StringIO.StringIO()
  with zipfile.ZipFile(tmp_space, mode='w') as zf:
    zipdir('.', zf)

  print 'generating function on lambda'
  result = client.create_function(FunctionName=job_name,
                                  Runtime='python2.7',
                                  Role=available_roles[picked_role-1]['Arn'],
                                  Handler=job_name+'.handler',
                                  Timeout=timeout,
                                  Code={'ZipFile': zip_full_directory()},
                                  Description=description)

  print 'writing out the .bada file'
  bada = {'name': job_name,
          'arn': result['FunctionArn']}
  with open(DOTFILE, 'w') as fh:
    fh.write(json.dumps(bada))

if os.path.exists(DOTFILE):
  print 'dotfile found, looking at command line arguments ...'

  try:
    argument = sys.argv[1]
  except:
    print "Command line option required: deploy, test"
    sys.exit()

  with open(DOTFILE, 'r') as fh:
    contents = fh.read()
  configuration = json.loads(contents)

  if argument in ('deploy', 'bing'):
    print 'deploying code for job %s' % configuration['name']
    client.update_function_code(FunctionName=configuration['arn'],
                                ZipFile=zip_full_directory())

else:
  make_new_lambda_function()