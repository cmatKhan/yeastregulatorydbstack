from aws_cdk import CfnOutput, Stack, Tags, aws_ec2, aws_elasticloadbalancingv2
from constructs import Construct


class ALBStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.Vpc,
        ssl_certificate_arn: str,
        django_target_group: aws_elasticloadbalancingv2.ApplicationTargetGroup,
        flower_target_group: aws_elasticloadbalancingv2.ApplicationTargetGroup,
        **kwargs
    ) -> None:
        """Create an Application Load Balancer with HTTP and HTTPS listeners.

        The following additional keyword arguments are configured:

        - name: The name of the load balancer. Default is the value
          of `id`.
        - alb_security_groups: A list of security groups to associate with the
          load balancer. Must be passed as a list. Default is an empty list.

        :param scope: See VPCStack class docstring for more information.
        :type scope: core.Construct
        :param id: See VPCStack class docstring for more information.
        :type id: str
        :param vpc: See SecurityGroupStack class docstring for more information.
        :type vpc: aws_ec2.Vpc
        :param ssl_certificate_arn: The ARN of the SSL certificate from AWS
          Certificate Manager.
          eg arn:aws:acm:us-east-2:040367161929:certificate/63b33893-d593-4ae0-8f34-c09b2ee96cad
        :type ssl_certificate_arn: str

        Example:

        .. code-block:: python

            import aws_cdk as cdk

            # Example usage within the same AWS CDK app
            app = cdk.App()
            vpc_stack = VPCStack(app, "VPCStack", env={"region": "us-east-2"})
            alb_stack = ALBStack(
              app, "DjangoLoadBalancer",
              vpc=vpc_stack.vpc,
              ssl_certificate_arn="arn:aws:acm:us-east-2:040367161929:certificate/63b33893-d593-4ae0-8f34-c09b2ee96cad",
              env={"region": "us-east-2"})
            app.synth()
        """
        # extract custom kwargs for this local class
        alb_security_groups = kwargs.pop("alb_security_groups", None)
        load_balancer_id = kwargs.pop("load_balancer_id", id + "-alb")
        domain = kwargs.pop("domain_name", "my-domain.com")
        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")
        # call the parent class constructor
        super().__init__(scope, id, **kwargs)

        self.alb = aws_elasticloadbalancingv2.ApplicationLoadBalancer(
            self,
            load_balancer_id,
            vpc=vpc,
            internet_facing=True,
            security_group=alb_security_groups,
        )

        # Add an HTTP listener that redirects to HTTPS
        http_listener = self.alb.add_listener(
            "HttpListener",
            port=80,
            default_action=aws_elasticloadbalancingv2.ListenerAction.redirect(
                port="443", protocol="HTTPS", permanent=True
            ),
        )

        # Add an HTTPS listener
        https_listener = self.alb.add_listener(
            "HttpsListener",
            port=443,
            certificates=[
                aws_elasticloadbalancingv2.ListenerCertificate(ssl_certificate_arn)
            ],
            default_action=aws_elasticloadbalancingv2.ListenerAction.forward(
                target_groups=[django_target_group]
            ),
        )

        # Listener Rule for the Flower Dashboard
        flower_rule = aws_elasticloadbalancingv2.ApplicationListenerRule(
            self,
            "FlowerRule",
            listener=https_listener,
            priority=5,  # Ensure the priority does not conflict with other rules
            conditions=[
                aws_elasticloadbalancingv2.ListenerCondition.host_headers(
                    ["flower." + domain]
                )
            ],
            action=aws_elasticloadbalancingv2.ListenerAction.forward(
                target_groups=[flower_target_group]
            ),
        )

        for resource in [self.alb]:
            Tags.of(resource).add(app_tag_name, app_tag_value)

        # Outputs
        CfnOutput(self, "LoadBalancerDNSName", value=self.alb.load_balancer_dns_name)
