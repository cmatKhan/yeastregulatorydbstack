from aws_cdk import CfnOutput, Stack, Tags
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class VPCStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        """
        Create a VPC with public and private subnets in all AZs.

        Note: There is 1 NAT gateway that is set up in one of the subnets
        and serves all private subnets.

        The following additional keyword arguments are configured:

        - vpc_name: The name of the VPC. Default is "MyVPC".
        - max_azs: The maximum number of AZs to use. Default is 99, which
          will create public and private subnets in each of the available AZs.
        - app_tag_name: The name of the tag to apply to all resources. Default
          is "app".
        - app_tag_value: The value of the tag to apply to all resources. Default
          is "myapp".

        :param scope: The scope in which to define this construct. This is the
          construct within which the new construct will be defined. Its purpose
          is to provide a context for constructs to exist within, which enables
          the CDK to understand the hierarchical structure of constructs. This
          context is used for various aspects of the CDK, including but not
          limited to, resource dependency management, logical grouping of
          related resources, and default configuration inheritance. The scope
          is typically an instance of a `Stack` or another `Construct`,
          serving as the parent in the construct tree hierarchy. Every
          construct must belong to a scope, and it can access the AWS resources
          and other constructs within the same scope or in parent scopes.
        :type scope: Construct
        :param id: A scope-unique id for the construct. This creates a unique
          identifier for the construct within the scope of the parent. It is
          used to generate unique construct names, which is useful for
          referencing resources in the AWS CloudFormation template. It is
          recommended to use lower-case alphanumeric characters and hyphens to
          ensure the id is unique within the scope of the parent construct.
        :type id: str

        Example:

        .. code-block:: python

            import aws_cdk as cdk

            # Entry point for the CDK app to instantiate the stack
            app = cdk.App()
            VPCStack(app, "VPCStack", env={"region": "us-east-2"})
            app.synth()
        """
        # extract custom kwargs for this local class
        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")
        max_azs = kwargs.pop("max_azs", 99)
        vpc_name = kwargs.pop("vpc_name", "MyVPC")

        # call the parent constructor
        super().__init__(scope, id, **kwargs)

        # Define the VPC
        self.vpc = ec2.Vpc(
            self,
            vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("172.31.0.0/16"),
            max_azs=max_azs,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=20,
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=20,
                ),
            ],
            nat_gateways=1,
        )

        # Tag all VPC resources
        Tags.of(self.vpc).add(app_tag_name, app_tag_value)

        # Outputs
        CfnOutput(self, "VPCId", value=self.vpc.vpc_id)

        for i, subnet in enumerate(self.vpc.public_subnets, start=1):
            CfnOutput(self, f"PublicSubnet{i}Id", value=subnet.subnet_id)

        for i, subnet in enumerate(self.vpc.private_subnets, start=1):
            CfnOutput(self, f"PrivateSubnet{i}Id", value=subnet.subnet_id)
