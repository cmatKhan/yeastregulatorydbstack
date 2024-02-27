from aws_cdk import Stack, Tags, aws_ec2
from constructs import Construct


class SecurityGroupStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: aws_ec2.Vpc, **kwargs) -> None:
        """_summary_

        :param scope: See VPCStack class docstring for more information.
        :type scope: Construct
        :param id: See VPCStack class docstring for more information.
        :type id: str
        :param vpc: The VPC to create the security groups in. This will likely
          be the VPC created in the VPCStack. `vpc` is an attribute of an
          an instance of VPCStack.
        :type vpc: ec2.Vpc

        Example:

        .. code-block:: python

            import aws_cdk as cdk

            # Example usage within the same AWS CDK app
            app = cdk.App()
            vpc_stack = VPCStack(app, "VPCStack", env={"region": "us-east-2"})
            security_group_stack = SecurityGroupStack(
              app, "SecurityGroupStack",
              vpc=vpc_stack.vpc, env={"region": "us-east-2"})
            app.synth()
        """
        # extract custom kwargs for this local class
        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")

        # call the parent constructor
        super().__init__(scope, id, **kwargs)

        # Django Security Group
        self.django_sg = aws_ec2.SecurityGroup(
            self,
            "DjangoSecurityGroup",
            vpc=vpc,
            description="Security group for Django ECS service allowing HTTP and HTTPS traffic",
        )

        # Redis Security Group
        self.redis_sg = aws_ec2.SecurityGroup(
            self,
            "RedisSecurityGroup",
            vpc=vpc,
            description="Security group for Redis service",
        )
        self.redis_sg.add_ingress_rule(
            self.django_sg,
            aws_ec2.Port.tcp(6379),
            "Allow Redis traffic from Django security group",
        )

        # Postgres Security Group
        self.postgres_sg = aws_ec2.SecurityGroup(
            self,
            "PostgresSecurityGroup",
            vpc=vpc,
            description="Security group for Postgres database",
        )
        self.postgres_sg.add_ingress_rule(
            self.django_sg,
            aws_ec2.Port.tcp(5432),
            "Allow PostgreSQL traffic from Django security group",
        )

        self.alb_security_group = aws_ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=vpc,
            description="Security group for ALB allowing HTTP and HTTPS traffic",
            security_group_name="DjangoStackLoadBalancerSecurityGroup",
        )

        self.alb_security_group.add_ingress_rule(
            aws_ec2.Peer.any_ipv4(),
            aws_ec2.Port.tcp(80),
            "Allow HTTP traffic from anywhere",
        )
        self.alb_security_group.add_ingress_rule(
            aws_ec2.Peer.any_ipv4(),
            aws_ec2.Port.tcp(443),
            "Allow HTTPS traffic from anywhere",
        )

        for resource in [
            self.django_sg,
            self.redis_sg,
            self.postgres_sg,
            self.alb_security_group,
        ]:
            Tags.of(resource).add(app_tag_name, app_tag_value)
