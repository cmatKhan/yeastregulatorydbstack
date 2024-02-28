#!/usr/bin/env python3
import os

import aws_cdk as cdk

from yeastregulatorydbstack import (
    ALBStack,
    DjangoServiceStack,
    LogGroupStack,
    RDSStack,
    RedisStack,
    RolesStack,
    SecurityGroupStack,
    TargetGroupStack,
    VPCStack,
)

app = cdk.App()

common_kwargs = {
    "app_tag_name": "app",
    "app_tag_value": "yeastregulatorydb",
}

ssl_arn = "arn:aws:acm:us-east-2:040367161929:certificate/63b33893-d593-4ae0-8f34-c09b2ee96cad"

django_image_uri = "040367161929.dkr.ecr.us-east-2.amazonaws.com/django-stack:latest"

vpc_stack = VPCStack(app, "VPCStack", **common_kwargs)

securitygroup_stack = SecurityGroupStack(
    app, "SecurityGroupStack", vpc_stack.vpc, **common_kwargs
)


roles_stack = RolesStack(app, "RolesStack", **common_kwargs)

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

redis_stack = RedisStack(
    app, "RedisStack", vpc_stack.vpc, securitygroup_stack.redis_sg, **common_kwargs
)

rds_stack = RDSStack(
    app, "RDSStack", vpc_stack.vpc, securitygroup_stack.postgres_sg, **common_kwargs
)

log_group_stack = LogGroupStack(
    app, "DjangoLogGroupStack", "DjangoLogGroupStack", **common_kwargs
)

django_service_stack = DjangoServiceStack(
    app,
    "DjangoServiceStack",
    vpc_stack.vpc,
    django_image_uri,
    "yeastregulatorydb",
    roles_stack.execution_role,
    roles_stack.task_role,
    redis_stack.cache_cluster,
    rds_stack.db_proxy,
    rds_stack.db_secret,
    log_group_stack.log_group,
    securitygroup_stack.django_sg,
    alb_stack.https_listener,
    s3_bucket="yeastregulatorydb-strides-tmp",
    env_filename=".env",
    **common_kwargs
)

app.synth()
