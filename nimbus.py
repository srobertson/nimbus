"""
Nimbus: manage AWS Cloudformation stacks with python


Usage: 
  nimbus templates
  nimbus show <template>
  nimbus [options] list
  nimbus create [--prompt] <stack> [template]
  nimbus update [--prompt] <stack> [template]
  nimbus destroy [--force] <stack>
  nimbus help

Options:
--aws-access-key=KEY        AWS key
--aws-secret=SECRET         AWS Secret

Details:

  nimbus templates                  -- list all the defined templates

  nimbus show <template>            -- output the template in json

  nimbus list                       -- show running stacks

  nimbus create <stack> [template]  -- create stack with the given name <stack>
                                     template required if more than one 
                                     template is defined in your nimbusfile

  nimbus update <stack>             -- update the running stack with the current
                                    template (for more info: see AWS guide on 
                                    updating running stacks)

  nimbus destroy <stack>            -- stop the running stack and delete all it's Resources

  nimbus help                       -- display this message


Environment Variables:
  AWS_ACCESS_KEY_ID         # You're amazon access key
  aws_secret_access_key     # You're amazon secret
  AWS_NOTIFICATION_ARNS     # List of aws notifications ARNs

"""

import os
import json
import sys

from collections import defaultdict
from copy import deepcopy

from boto.cloudformation.connection import CloudFormationConnection
from boto.exception import BotoServerError
from docopt import docopt


def main():

  arguments = docopt(__doc__, version='Nimbus')
  action = action_from(arguments)
  prompt = arguments['--prompt']
  force  = arguments['--force']
  stack_name = arguments['<stack>']

  aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
  aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
  aws_notification_arns = maybe(
    listify,
    os.environ.get('AWS_NOTIFICATION_ARNS')
  )

  conn = CloudFormationConnection(aws_access_key_id, aws_secret_access_key)

  wd = os.getcwd()
  try:
    sys.path.append(wd)
    import nimbusfile
    print "Loaded {}".format(nimbusfile.__file__)
  except ImportError:
    print "No nimbusfile found at {}.".format(wd)
    sys.exit(2)

  template = arguments['<template>'] or default_template()

  if action in ("create", "update"):
    parameters = StackParameters.params_by_stack.get(stack_name, {})
    if prompt:
      for parameter, props in StackTemplate.templates[template]['Parameters'].items():
        parameters[parameter] = raw_input("{Description} [{Default}]: ".format(**props)) or props['Default']
    
    method = getattr(conn,"{0}_stack".format(action))

    try:      
      method(stack_name, 
        template_body=StackTemplate.output(template),
        parameters=parameters.items(),
        capabilities=["CAPABILITY_IAM"],
        disable_rollback=True,
        notification_arns=aws_notification_arns
      )
    except BotoServerError, e:
      print(json.loads(e.error_message)["Error"]["Message"])
      sys.exit(1)
  elif action == 'show':
    # Display the content of the given template
    show_template(template)
  elif action == "destroy":    
    if force:
      cont = 'y'
    else:
      cont = raw_input("Delete stack {0} [y/N] ".format(stack_name))

    if cont.lower().strip() == 'y':
      print conn.delete_stack(stack_name)
  elif action == "list":
    show_stacks(conn)
  elif action == 'templates':
    show_templates()
  elif action == 'help':
    show_help()
    sys.exit(1)

def action_from(arguments):
  # return the first arument that starts with a letter
  # and evalates to true
  for k,value in arguments.items():
    if k[0].isalpha() and value:
      return k

def default_template():
  # icky: unpure
  return StackTemplate.templates.keys()[0]


def show_stacks(conn):
  for stack in conn.describe_stacks():
    if stack.stack_name: # not sure why stack_name is sometimes none
      print stack.stack_name, "\t", stack.stack_status

def show_templates():
  print
  print "Templates"
  print "========="
  for t in StackTemplate.templates.keys():
    print t
  if len(StackTemplate.templates.keys()) == 0:
    print "(no templates defined)"
  print

def show_template(template):
  print StackTemplate.output(template)

def show_help():
  print __doc__



marker = ()
class Fragment(dict):
  def mutate(self, mutations, value=marker):
    """Returns a copy of the template substituting the value for the pathe specified"""
    
    if value is not marker:
      mutations = {mutations: value}
    
    copy = deepcopy(self)
    
    for path, value in mutations.items():
      node = copy
      for part in path[:-1]:
        node = node[part]
      node[path[-1]] = value
    return copy

class StackParameters(object):
  params_by_stack = {}
  def __init__(self, stack_name, **kw):
    self.params_by_stack[stack_name] = kw

class StackTemplate(object):
  templates = {}
  @classmethod
  def output(cls, stack_name):
    return json.dumps(cls.templates[stack_name], indent=2, cls=StackTemplateEncoder)
    
    
  def __init__(self, name):
    self.name = name
      
  def __enter__(self):
    StackTemplate.current = self.templates[self.name] = defaultdict(dict, {"AWSTemplateFormatVersion": "2010-09-09"})

  def __exit__(self, type, value, tb):
    StackTemplate.current = None


class StackTemplateEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Part):
      return dict(Ref=obj.ref)
  
      
class Part(object):
  section = None
  def __init__(self, ref, **kw):
    self.ref = ref
    if self.section == None:
      raise RuntimeError
      
    StackTemplate.current[self.section][ref] = dict(kw)
    
  def __getattr__(self, attr):
    return {"Fn::GetAtt" : [self.ref, attr]}

class Description(Part):
  def __init__(self, description):
    StackTemplate.current['Description']=description

class Mapping(Part):
  section = "Mappings"
  def __init__(self, ref, map):
    # maps takes a singel argument the map. Can't use key word args
    # here as some of the keys allowed in maps may contain characters
    # that are invalid in python
    self.ref = ref
    StackTemplate.current[self.section][ref] = map
    
class Output(Part):
  section = "Outputs"

    
class Parameter(Part):
  section = "Parameters"

class Resource(Part):
  section = "Resources"

def maybe(f, value):
  if value is not None:
    return f(value)

def either(left, right, value):
  if value[1] is not None:
    return right(value[1])
  else:
    return left(value[0])

def listify(value):
  return [value]

