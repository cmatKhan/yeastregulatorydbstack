from aws_cdk import Stack, Tags, aws_iam
from constructs import Construct


class RolesStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:

        # extract custom kwargs for this local class
        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")

        # call the parent constructor
        super().__init__(scope, id, **kwargs)

        # MyDBProxyRole
        self.db_proxy_role = aws_iam.Role(
            self,
            "MyDBProxyRole",
            assumed_by=aws_iam.ServicePrincipal("rds.amazonaws.com"),
            description="Allows RDS to assume for DB Proxy",
            inline_policies={
                "RDSProxyPolicy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetSecretValue",
                                "secretsmanager:DescribeSecret",
                            ],
                            resources=["*"],
                            effect=aws_iam.Effect.ALLOW,
                        )
                    ]
                )
            },
        )

        # ExecutionRole
        self.execution_role = aws_iam.Role(
            self,
            "ExecutionRole",
            assumed_by=aws_iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Execution role for ECS tasks",
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
            inline_policies={
                "CustomExecutionPolicy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "ecs:StartTask",
                                "ecs:StopTask",
                                "ecs:DescribeTasks",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:CreateLogGroup",
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "s3:GetObject",
                            ],
                            resources=["*"],
                            effect=aws_iam.Effect.ALLOW,
                        )
                    ]
                )
            },
        )

        # TaskRole
        self.task_role = aws_iam.Role(
            self,
            "TaskRole",
            assumed_by=aws_iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Task role for ECS tasks",
            inline_policies={
                "DjangoAppPolicy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "s3:*",
                                "rds:*",
                                "secretsmanager:GetSecretValue",
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=["*"],
                            effect=aws_iam.Effect.ALLOW,
                        )
                    ]
                )
            },
        )

        for resource in [self.db_proxy_role, self.execution_role, self.task_role]:
            Tags.of(resource).add(app_tag_name, app_tag_value)
