```
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

  nimbus list                       -- show running stack_stacks

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
```