#!/usr/bin/env python3
import os

import aws_cdk as cdk

from yeastregulatorydbstack import (ALBStack, RDSStack, RedisStack, RolesStack,
                                    SecurityGroupStack, TargetGroupStack,
                                    VPCStack)

app = cdk.App()

common_kwargs = {
    "app_tag_name": "app",
    "app_tag_value": "yeastregulatorydb",
}

ssl_arn = "arn:aws:acm:us-east-2:040367161929:certificate/63b33893-d593-4ae0-8f34-c09b2ee96cad"

vpc_stack = VPCStack(app, "VPCStack", **common_kwargs)

securitygroup_stack = SecurityGroupStack(
    app, "SecurityGroupStack", vpc_stack.vpc, **common_kwargs
)

targetgroup_stack = TargetGroupStack(
    app, "TargetGroupStack", vpc_stack.vpc, **common_kwargs
)

alb_stack = ALBStack(
    app,
    "ALBStack",
    vpc_stack.vpc,
    ssl_arn,
    targetgroup_stack.django_target_group,
    targetgroup_stack.flower_target_group,
    alb_security_groups=securitygroup_stack.alb_security_group,
    **common_kwargs
)  # os.environ["SSL_CERTIFICATE_ARN", ssl_arn]

roles_stack = RolesStack(app, "RolesStack",  **common_kwargs)


app.synth()
