'''
clamda is stupid a command line tool
for working with aws lambda and making
the dev workflow better 

       _.---._
   .:":(O)'(O)":.
  :` _'\_____/_.':
  '`.`._`-.-'_.'.''
   `.`-.`-.-'.-'.'
    `._`-.-'_.'
        `''``ms  

ie tests
'''
import select
import boto3
import json
import os
import zipfile
import StringIO
import sys
import base64

DOTFILE = '.clamda'
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

  print 'writing out the .clamda file'
  clamda = {'name': job_name,
            'arn': result['FunctionArn']}
  with open(DOTFILE, 'w') as fh:
    fh.write(json.dumps(clamda))

def get_configuration():
  ''' open the dotfile in the folder and grab the configuration out of it '''
  if os.path.exists(DOTFILE):
    with open(DOTFILE, 'r') as fh:
      contents = fh.read()
    configuration = json.loads(contents)
    return configuration
  else:
    return False

def run_tests():
  ''' open up the tests/ folder, find any assertions in there and 
  execute them by calling the invoke method and comparing the output
  to expected output. note that a test will consist of an input json
  and then an output json '''

def invoke(configuration, text):
  ''' just invoke the function with some text '''
  inv = client.invoke(FunctionName=configuration['arn'],
                      LogType='Tail',
                      Payload=text)
  base64_logs = base64.b64decode(inv['LogResult'])
  print "----- LOGS ------- "
  print base64_logs
  print "----- RESULT ----- "
  print inv['Payload'].read()

def find_errors(name):
  client = boto3.client('logs')
  
  log_name = '/aws/lambda/' + name
  streams = client.describe_log_streams(logGroupName=log_name,
                                        descending=True,
                                        orderBy='LastEventTime')
  all_streams = streams['logStreams']
  stream_ids = [a['logStreamName'] for a in all_streams]
  match = client.filter_log_events(logGroupName=log_name,
                                   logStreamNames=stream_ids,
                                   filterPattern='Error')
  for event in match['events']:
    print '-------ERROR------'
    print event['message']

def tail_logs(name):
  client = boto3.client('logs')

  log_name = '/aws/lambda/' + name
  streams = client.describe_log_streams(logGroupName=log_name,
                                        descending=True,
                                        orderBy='LastEventTime')
  all_streams = streams['logStreams']
  stream_ids = [a['logStreamName'] for a in all_streams]
  event_count = 0
  stream_id = stream_ids[0]
  logs = client.get_log_events(logGroupName=log_name,
                               logStreamName=stream_id,
                               startFromHead=False,
                               limit=1000)
  events = logs['events']
  for event in events:
    event_count += 1
    print event['message']

def main():
  configuration = get_configuration()
  try:
    argument = sys.argv[1]
  except:
    help()
    sys.exit()

  if configuration is not False and argument in ('deploy'):
    print 'deploying code for job %s' % configuration['name']
    client.update_function_code(FunctionName=configuration['arn'],
                                ZipFile=zip_full_directory())
  elif configuration is not False and argument in ('test'):
    print 'Running tests for lambda job'
    run_tests(configuration)
  elif configuration is not False and argument in ('invoke'):
    if select.select([sys.stdin,],[],[],0.0)[0]:
      invoke_text = sys.stdin
    else:
      invoke_text = sys.argv[2]
    invoke(configuration, invoke_text)
  elif configuration is not False and argument in ('errors'):
    print "searching logs for errors"
    find_errors(configuration['name'])
  elif configuration is not False and argument in ('tail'):
    tail_logs(configuration['name'])
  elif configuration is False and argument in ('init'):
    print 'initializing new lambda job'
    make_new_lambda_function()
  else:
    help()

def help():
  print '''Available command line arguments 
              clamda init - initialize new lambda job
              clamda deploy - zip & deploy current job
              clamda errors - find errors in cloudwatch logs
              clamda tail - spit out tailed logs from cloudwatch
              clamda invoke "{json}" - invoke the function with some json
              clamda test - run tests over assertions in tests/ folder'''

if __name__ == '__main__':  
  main()
