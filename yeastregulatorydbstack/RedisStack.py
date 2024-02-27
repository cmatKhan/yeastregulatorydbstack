from aws_cdk import CfnOutput, Stack, Tags, aws_ec2, aws_elasticache
from constructs import Construct


class RedisStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.Vpc,
        redis_security_group_id: aws_ec2.SecurityGroup,
        **kwargs
    ) -> None:

        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")

        super().__init__(scope, id, **kwargs)

        # Assuming the VPC and subnets are passed as arguments
        subnet_group = aws_elasticache.CfnSubnetGroup(
            self,
            "MyElastiCacheSubnetGroup",
            description="Subnet group for ElastiCache",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
        )

        self.cache_cluster = aws_elasticache.CfnCacheCluster(
            self,
            "MyElastiCacheRedis",
            cache_node_type="cache.t2.micro",
            engine="redis",
            num_cache_nodes=1,
            cache_subnet_group_name=subnet_group.ref,
            vpc_security_group_ids=[redis_security_group_id],
        )

        for resource in [self.cache_cluster, subnet_group]:
            Tags.of(resource).add(app_tag_name, app_tag_value)

        CfnOutput(self, "RedisClusterId", value=self.cache_cluster.ref)
