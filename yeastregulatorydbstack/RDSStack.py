from aws_cdk import (
    CfnOutput,
    Stack,
    Tags,
    aws_ec2,
    aws_iam,
    aws_rds,
    aws_secretsmanager,
)
from constructs import Construct


class RDSStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.IVpc,
        db_proxy_role: aws_iam.Role,
        **kwargs
    ):
        """Create a PostgreSQL RDS instance and RDS Proxy

        The following additional keyword arguments are configured:

        - app_tag_name: The name of the tag to apply to all resources. Default
            is "app".
        - app_tag_value: The value of the tag to apply to all resources. Default
            is "myapp".
        - max_connections: The maximum number of connections to the database.
            Default is "200".

        :param scope: See VPCStack class docstring for more information.
        :type scope: Construct
        :param id: See VPCStack class docstring for more information.
        :type id: str
        :param vpc: See SecurityGroupStack class docstring for more information.
        :type vpc: aws_ec2.IVpc
        :param db_proxy_role: The IAM role for the RDS Proxy. This will likely
            be the role created in the RolesStack. `db_proxy_role` is an
            attribute of an instance of RolesStack.
        :type db_proxy_role: aws_iam.Role
        """

        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")
        max_connections = kwargs.pop("max_connections", "200")

        super().__init__(scope, id, **kwargs)

        # DB Secret for storing the master username and password
        self.db_secret = aws_secretsmanager.Secret(
            self,
            "MyDBSecret",
            description="RDS database credentials",
            generate_secret_string=aws_secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "postgres"}',
                generate_string_key="password",
                exclude_characters="/@\" '",
                password_length=16,
            ),
        )

        # Custom Parameter Group
        custom_parameter_group = aws_rds.ParameterGroup(
            self,
            "MyCustomParameterGroup",
            engine=aws_rds.DatabaseInstanceEngine.postgres(
                version=aws_rds.PostgresEngineVersion.VER_15_2
            ),
            parameters={"max_connections": max_connections},
        )

        # DB Subnet Group
        db_subnet_group = aws_rds.SubnetGroup(
            self,
            "MyDBSubnetGroup",
            description="My DB Subnet Group",
            vpc=vpc,
            vpc_subnets=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        # RDS Database Instance
        db_instance = aws_rds.DatabaseInstance(
            self,
            "MyDBInstance",
            engine=aws_rds.DatabaseInstanceEngine.postgres(
                version=aws_rds.PostgresEngineVersion.VER_15_2
            ),
            instance_type=aws_ec2.InstanceType.of(
                aws_ec2.InstanceClass.BURSTABLE2, aws_ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            credentials=aws_rds.Credentials.from_secret(self.db_secret),
            parameter_group=custom_parameter_group,
            subnet_group=db_subnet_group,
            allocated_storage=20,
        )

        # RDS Proxy
        db_proxy = aws_rds.DatabaseProxy(
            self,
            "MyDBProxy",
            proxy_target=aws_rds.ProxyTarget.from_instance(db_instance),
            secrets=[self.db_secret],
            vpc=vpc,
            role=db_proxy_role,
            db_proxy_name="mydbproxy",
            require_tls=False,
        )

        for resource in [
            self.db_secret,
            custom_parameter_group,
            db_subnet_group,
            db_instance,
            db_proxy,
        ]:
            Tags.of(resource).add(app_tag_name, app_tag_value)

        # Outputs
        CfnOutput(
            self, "RDSInstanceEndpoint", value=db_instance.db_instance_endpoint_address
        )
        CfnOutput(self, "RDSProxyEndpoint", value=db_proxy.endpoint)
