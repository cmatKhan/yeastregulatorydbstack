# Introduction

This is a CDK app that sets up a fully contained stack to run a django app with
a postgresql RDS and redis cache. The app is deployed to an ECS Fargate cluster
behind an Application Load Balancer. Celery is configured to run asynchronous
background tasks on a separate ECS Fargate cluster. The app is deployed to a
VPC with public and private subnets, the application load balancer redirects
HTTP traffic to HTTPS and the SSL/TLS certificate is managed by AWS Certificate
Manager. The load balancer IP can be provided to Route 53 to create a DNS
record for the app.

This is largely based on the following tutorial:

https://github.com/kokospapa8/ecs-fargate-sample-app/tree/master/config/cdk


https://kokospapa.notion.site/How-to-deploy-django-app-to-ECS-Fargate-Part1-a1e99c19b2a3423585e67f0b1ad81cbd

## Development installation

Fork the repo and clone it to your local machine. Note that I developed this
in python 3.10.13 and cdk 2.130.0. However, I had to downgrade requirements.txt
to use `aws-cdk-lib==2.117.0`. That may not be necessary.

The following assumes that you have AWS CLI and CDK installed and have a valid
profile to use with CDK.
See the instructions here: https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html

`cd` into the local repo directory and create a virtualenv on MacOS and Linux:

```bash
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```bash
$ source .venv/bin/activate
```

Once the virtualenv is activated, you can install the required dependencies.

```bash
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```bash
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation

## IMPORTANT CAVEATS

Right now, the production `/start` script does not call migrate and as a
result the database is not created. I have a workaround implemented where
psql actually checks for the database and then creates it, but that doesn't
create the user db, for instance. Better is to set up a one time task that
executes before everything else and calls migrate, etc.

Right now, because the task and django service are setup such that you can
exec into the task, you can do this:

```bash
aws ecs execute-command --profile chasem --cluster DjangoAppCluster \
                         --task $arn \
                         --container django \
                         --command "/bin/sh" \
                         --interactive \
                         --region us-east-2
```

where the `$arn` is the running task arn. Once there, you can do this:

```bash
/entrypoint python manage.py migrate`
```

or any other django management command.

## Lessons learned

1. In the CloudFormation json/yaml, you must manually define dependencies
   between resources using the `DependsOn` attribute. In CDK, there are
   two methods:
    * The first is to set the resources created in any given stack as
      properties of the stack object. Then, those can be used as arguments
      to the constructors of downstream stacks. The dependencies between
      stacks are automatically handled by CDK.
    * Another is to define the outputs/inputs of the Stack classes using CfnOutput
      and CfnInput classes. Then, the outputs of one stack can be used as
      inputs to another stack. This more explicitly defines the interface
      between Stack classes and allows those same Stack classes to be used
      across apps.

1. Elasticache pricing: https://aws.amazon.com/elasticache/pricing/ and a price
    calculator: https://calculator.aws/#/createCalculator/ElastiCache. Bottom
    line is that the Redis elasticache cluster with the smallest instance should
    be ~20 bucks a month

1. To generate logs from the RDS DB proxy, set `debug_logging=True` and then
    look in the cloudwatch log group for `/ecs/rds/proxy/<your-proxy-name>`.