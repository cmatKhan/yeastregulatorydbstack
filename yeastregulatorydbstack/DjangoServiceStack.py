from aws_cdk import (Aws, Stack, Tags, aws_ec2, aws_ecs, aws_elasticache,
                     aws_elasticloadbalancingv2, aws_iam, aws_logs, aws_rds,
                     aws_s3, aws_secretsmanager)
from constructs import Construct


class DjangoServiceStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.Vpc,
        image_uri: str,
        database_name: str,
        execution_role: aws_iam.Role,
        task_role: aws_iam.Role,
        redis_instance: aws_elasticache.CfnCacheCluster,
        db_proxy: aws_rds.CfnDBProxy,
        db_secret: aws_secretsmanager.Secret,
        log_group: aws_logs.LogGroup,
        security_group: aws_ec2.SecurityGroup,
        listener: aws_elasticloadbalancingv2.ApplicationListener,
        **kwargs
    ) -> None:
        """Create a Django ECS service

        The following additional keyword arguments are configured:

        - app_tag_name: The name of the tag to apply to all resources. Default
            is "app".
        - app_tag_value: The value of the tag to apply to all resources. Default
            is "myapp".
        - postgres_port: The port for the RDS database. Default is "5432".
        - s3_bucket: The S3 bucket to store the environment file. Default is
            None.
        - env_filename: The path to the environment file in the S3 bucket. Default
            is None.

        If s3_bucket and env_filename are passed, then an environment file will
        be used to set environment variables for the ECS service. If only one
        is passed, a ValueError will be raised. If neither is passed, then no
        environment file will be used.

        :param scope: See VPCStack class docstring for more information.
        :type scope: Construct
        :param id: See VPCStack class docstring for more information.
        :type id: str
        :param vpc: See SecurityGroupStack class docstring for more information.
        :type vpc: aws_ec2.Vpc
        :param image_uri: The URI of the Docker image to use for the ECS service.
            for docker up, the image_uri is the name of the image followed
            optionally by the tag, eg django:latest. For the AWS ECR, the image_uri
            is the URI of the image in the ECR repository,
            eg 123456789012.dkr.ecr.us-west-2.amazonaws.com/my-repository:latest
        :type image_uri: str
        :param execution_role: The role that the ECS service will assume to
            execute tasks.
        :type execution_role: aws_iam.Role
        :param task_role: The role that the ECS service will assume to execute
            tasks.
        :type task_role: aws_iam.Role
        :param redis_instance: The Elasticache Redis instance to connect to.
        :type redis_instance: aws_elasticache.CfnCacheCluster
        :param db_proxy: The RDS database proxy to connect to.
        :type db_proxy: aws_rds.CfnDBProxy
        :param db_secret: The RDS database secrets to connect to.
        :type db_secret: aws_secretsmanager.Secret
        :param log_group: The log group for the ECS service.
        :type log_group: aws_logs.LogGroup
        :param security_group: The security group for the ECS service.
        :type security_group: aws_ec2.SecurityGroup
        :param listener: The listener for the ECS service.
        :type listener: aws_elasticloadbalancingv2.ApplicationListener

        :raises ValueError: If `env_filename` is provided without `s3_bucket` or
            vice versa.
        """
        # Extract custom kwargs for this local class
        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")
        postgres_port = kwargs.pop("postgres_port", "5432")
        s3_bucket = kwargs.pop("s3_bucket", None)
        env_filename = kwargs.pop("env_filename", None)

        # Call the parent constructor
        super().__init__(scope, id, **kwargs)

        # note that this must be below the super() call b/c `self` is used
        if s3_bucket is None and env_filename is not None:
            raise ValueError(
                "If you provide an environment file path, you must also provide an S3 bucket."
            )
        if env_filename is None and s3_bucket is not None:
            raise ValueError(
                "If you provide an S3 bucket, you must also provide an environment file path."
            )
        if env_filename is not None and s3_bucket is not None:
            # Get a reference to the S3 bucket
            s3_bucket_obj = aws_s3.Bucket.from_bucket_name(
                self, "MyEnvFilesBucket", s3_bucket
            )
            # Use aws_ecs.EnvironmentFile.from_bucket to specify the environment file
            # construct as list due to input expected format to the task
            environment_file = [
                aws_ecs.EnvironmentFile.from_bucket(s3_bucket_obj, env_filename)
            ]
        else:
            environment_file = None

        # These environmental variables may be used to the celery services
        # these take precedence over the environment file
        # https://repost.aws/knowledge-center/ecs-task-environment-variables
        # NOTE: DJANGO_AWS_STORAGE_BUCKET_NAME is where file objects are stored
        # in the S3 bucket. AWS_STORAGE_BUCKET_NAME is used for the static files
        self.django_env_vars = {
            "AWS_DEFAULT_REGION": Aws.REGION,
            "AWS_S3_REGION_NAME": Aws.REGION,
            "REDIS_HOST": redis_instance.attr_redis_endpoint_address,
            "REDIS_PORT": str(redis_instance.attr_redis_endpoint_port),
            "POSTGRES_HOST": db_proxy.endpoint,
            "POSTGRES_PORT": postgres_port,
            "POSTGRES_DB": database_name,
            "DJANGO_DEBUG": "true",
            "WEB_CONCURRENCY": "1",
            "DJANGO_SECURE_SSL_REDIRECT": "False",
            "DJANGO_AWS_STORAGE_BUCKET_NAME": "yeastregulatorydb-strides-tmp",
            "AWS_STORAGE_BUCKET_NAME": "yeastregulatorydb-strides-test",
            "CONN_MAX_AGE": "60",
        }

        # Define the ECS Cluster
        cluster = aws_ecs.Cluster(
            self,
            "DjangoAppEcsCluster",
            vpc=vpc,
            cluster_name="DjangoAppCluster",
            enable_fargate_capacity_providers=True,
        )

        # Define the Task Definition
        task_definition = aws_ecs.FargateTaskDefinition(
            self,
            "DjangoTaskDefinition",
            cpu=1024,  # Example CPU units
            memory_limit_mib=2048,  # Example Memory
            execution_role=execution_role,
            task_role=task_role,
        )

        # Add container to the task definition
        container = task_definition.add_container(
            "django",
            image=aws_ecs.ContainerImage.from_registry(image_uri),
            command=["/start"],
            environment=self.django_env_vars,
            secrets={
                "POSTGRES_USER": aws_ecs.Secret.from_secrets_manager(
                    db_secret, field="username"
                ),
                "POSTGRES_PASSWORD": aws_ecs.Secret.from_secrets_manager(
                    db_secret, field="password"
                ),
            },
            environment_files=environment_file,
            logging=aws_ecs.LogDriver.aws_logs(
                stream_prefix="ecs", log_group=log_group
            ),
        )

        # Add port mappings if necessary
        container.add_port_mappings(
            aws_ecs.PortMapping(container_port=5000, protocol=aws_ecs.Protocol.TCP)
        )

        # Define the ECS Service
        service = aws_ecs.FargateService(
            self,
            "DjangoService",
            cluster=cluster,
            task_definition=task_definition,
            capacity_provider_strategies=[
                aws_ecs.CapacityProviderStrategy(capacity_provider="FARGATE", weight=1)
            ],
            desired_count=1,
            security_groups=[security_group],
            assign_public_ip=True,
            vpc_subnets=aws_ec2.SubnetSelection(
                subnets=[
                    vpc.select_subnets(subnet_type=aws_ec2.SubnetType.PUBLIC).subnets[0]
                ]
            ),
            task_definition_revision=aws_ecs.TaskDefinitionRevision.LATEST,
            enable_execute_command=True,
        )

        # Register the service with the HTTPS listener
        listener.add_targets(
            "DjangoTargets",
            priority=10,
            port=5000,
            protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTP,
            targets=[service],
            conditions=[
                aws_elasticloadbalancingv2.ListenerCondition.path_patterns(["/*"])
            ],
            health_check={"path": "/"},
        )

        # Add tags to resources
        for resource in [cluster, task_definition, service]:
            Tags.of(resource).add(app_tag_name, app_tag_value)
