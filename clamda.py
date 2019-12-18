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
import datetime
import boto3
import json
import os
import zipfile
from io import BytesIO
import sys
import base64
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DOTFILE = '.clamda'
DEFAULT_RUNTIME = 'python2.7'
DEFAULT_JOB = '''

def handler(event, context):
  pass

'''

client = boto3.client('lambda')
iam_client = boto3.client('iam')

# helper function to zip up an entire folder
def zipdir(path, ziph):
  for root, dirs, files in os.walk(path):
    for filename in files:
      ziph.write(os.path.join(root, filename))

def zip_full_directory():
  logger.info('zipping up folder contents...')
  tmp_space = BytesIO()
  with zipfile.ZipFile(tmp_space, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    zipdir('.', zf)
  return tmp_space.getvalue()

def make_new_lambda_function():
  logger.info('''Looks like a dotfile doesn't exist for this folder, let's instantiate a job...''')

  # get roles
  role_data = iam_client.list_roles()
  available_roles = role_data['Roles']

  job_name = input("Lambda Job Name: ")

  i = 1
  for role in available_roles:
    logger.info("(%s) %s %s" % (i, role['RoleName'], role['Arn']))
    i += 1

  picked_role = int(input("Pick IAM Role: "))
  description = input("Enter Description: ")
  timeout = input("Timeout (default = 3s): ")
  create_job = input("Would you like to create a new job file (Y/N)?: ")

  try:
    timeout = int(timeout)
  except:
    timeout = 3

  # create the job if the creator wants to
  if create_job in ('Y', 'y'):
    logger.info("Creating empty job file..")
    with open(job_name + '.py', 'w') as fh:
      fh.write(DEFAULT_JOB)

  # now zip up the contents of this folder
  logger.info('zipping up folder contents...')
  tmp_space = BytesIO()
  with zipfile.ZipFile(tmp_space, mode='w') as zf:
    zipdir('.', zf)

  logger.info('generating function on lambda')
  result = client.create_function(FunctionName=job_name,
    Runtime=DEFAULT_RUNTIME,
    Role=available_roles[picked_role-1]['Arn'],
    Handler=job_name+'.handler',
    Timeout=timeout,
    Code={'ZipFile': zip_full_directory()},
    Description=description)

  logger.info('writing out the .clamda file')
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
  logger.info(base64_logs.decode('utf-8'))
  response_payload = inv['Payload'].read().decode('utf-8')
  print(response_payload)

def find_errors(name):
  search_logs(name, 'Error')
  search_logs(name, 'Exception')
  search_logs(name, 'Timeout')
  search_logs(name, 'Expiration')

def search_logs(name, filter_pattern):
  client = boto3.client('logs')
  
  log_name = '/aws/lambda/' + name
  streams = client.describe_log_streams(logGroupName=log_name,
    descending=True, orderBy='LastEventTime')
  all_streams = streams['logStreams']
  stream_ids = [a['logStreamName'] for a in all_streams]
  nextToken = True

  match = client.filter_log_events(logGroupName=log_name,
                                   logStreamNames=stream_ids,
                                   filterPattern=filter_pattern)
  events = match.get('events')
  nextToken = match.get('nextToken')

  # more logs to search
  while nextToken:
    match = client.filter_log_events(logGroupName=log_name,
                                     nextToken=nextToken,
                                     logStreamNames=stream_ids,
                                     filterPattern=filter_pattern)
    events = events + match.get('events')
    nextToken = match.get('nextToken')

  for event in events:
    timestamp = event['timestamp'] / 1000
    human_date = datetime.datetime.fromtimestamp(int(timestamp))
    message = event['message'].strip()
    logger.info('\t'.join((human_date.strftime('%Y-%m-%d %H:%M:%S'), message)))

def find_durations(name):
  search_logs(name, 'REPORT RequestId')

def list_env_vars(name):
  resp = client.get_function(FunctionName=name)
  config = resp['Configuration']
  env = config.get('Environment', {})
  env_vars = env.get('Variables', {})
  for (k,v) in env_vars.items():
    logger.info("ENV VARIABLE: %s = %s" % (k,v))
  return env_vars

def set_env_var(name, key, value):
  current_vars = list_env_vars(name)
  current_vars[key] = value
  client.update_function_configuration(FunctionName=name,
                                       Environment={'Variables': current_vars})

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
                               startFromHead=False)
  events = logs['events']
  for event in events:
    event_count += 1
    print(event['message'])

def main():
  configuration = get_configuration()
  try:
    argument = sys.argv[1]
    addl_arguments = sys.argv[2:]
  except:
    help()
    sys.exit()

  if configuration is not False and argument in ('deploy'):
    logger.info('deploying code for job %s' % configuration['name'])
    client.update_function_code(FunctionName=configuration['arn'],
                                ZipFile=zip_full_directory())
  elif configuration is not False and argument in ('test'):
    logger.info('Running tests for lambda job')
    run_tests(configuration)
  elif configuration is not False and argument in ('invoke'):
    if select.select([sys.stdin,],[],[],0.0)[0]:
      invoke_text = sys.stdin.read()
    else:
      invoke_text = sys.argv[2]
    invoke(configuration, invoke_text)
  elif configuration is not False and argument in ('lsenv'):
    list_env_vars(configuration['name'])
  elif configuration is not False and argument in ('setenv'):
    logger.info("setting env var ")
    var_key = addl_arguments[0]
    var_val = addl_arguments[1]
    set_env_var(configuration['name'], var_key, var_val)
  elif configuration is not False and argument in ('search'):
    query = sys.argv[2]
    search_logs(configuration['name'], query)
  elif configuration is not False and argument in ('errors'):
    logger.info("searching logs for errors")
    find_errors(configuration['name'])
  elif configuration is not False and argument in ('durations', 'duration'):
    find_durations(configuration['name'])
  elif configuration is not False and argument in ('tail'):
    tail_logs(configuration['name'])
  elif configuration is False and argument in ('init'):
    logger.info('initializing new lambda job')
    make_new_lambda_function()
  else:
    help()

def help():
  print('''Available command line arguments 
              clamda init - initialize new lambda job
              clamda deploy - zip & deploy current job
              clamda durations - view duration of jobs
              clamda setenv KEY VAL - set lambda env var
              clamda lsenv - list environmental vars
              clamda errors - find errors in cloudwatch logs
              clamda tail - spit out tailed logs from cloudwatch
              clamda invoke "{json}" - invoke the function with some json
              clamda search "term" - search the logs for a custom search term
              clamda test - run tests over assertions in tests/ folder''')

if __name__ == '__main__':  
  main()
