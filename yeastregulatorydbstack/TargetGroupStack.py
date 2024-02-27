from aws_cdk import Stack, Tags, aws_ec2, aws_elasticloadbalancingv2
from constructs import Construct


class TargetGroupStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: aws_ec2.Vpc, **kwargs):
        """Create target groups

        :param scope: See VPCStack class docstring for more information.
        :type scope: Construct
        :param id: See VPCStack class docstring for more information.
        :type id: str
        :param vpc: The VPC to create the security groups in. This will likely
            be the VPC created in the VPCStack. `vpc` is an attribute of an
            instance of VPCStack.
        :type vpc: aws_ec2.Vpc

        Example:

        .. code-block:: python

                import aws_cdk as cdk

                # Example usage within the same AWS CDK app
                app = cdk.App()
                vpc_stack = VPCStack(app, "VPCStack", env={"region": "us-east-2"})
                target_group_stack = TargetGroupsStack(
                app, "TargetGroupStack",
                vpc = vpc_stack.vpc)
                app.synth()
        """
        # extract custom kwargs for this local class
        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")

        # call the parent constructor
        super().__init__(scope, id, **kwargs)

        # Django Target Group
        self.django_target_group = aws_elasticloadbalancingv2.ApplicationTargetGroup(
            self,
            "DjangoTargetGroup",
            vpc=vpc,
            port=5000,
            protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTP,
            target_type=aws_elasticloadbalancingv2.TargetType.IP,
            health_check=aws_elasticloadbalancingv2.HealthCheck(
                protocol=aws_elasticloadbalancingv2.Protocol.HTTP,
                path="/healthcheck",
            ),
        )

        # Flower Target Group
        self.flower_target_group = aws_elasticloadbalancingv2.ApplicationTargetGroup(
            self,
            "FlowerTargetGroup",
            vpc=vpc,
            port=5555,  # Assuming default port for Flower is 5555
            protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTP,
            target_type=aws_elasticloadbalancingv2.TargetType.IP,
            health_check=aws_elasticloadbalancingv2.HealthCheck(
                protocol=aws_elasticloadbalancingv2.Protocol.HTTP,
                path="/health",
            ),
        )

        for resource in [self.django_target_group, self.flower_target_group]:
            Tags.of(resource).add(app_tag_name, app_tag_value)
