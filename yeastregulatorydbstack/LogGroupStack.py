from aws_cdk import RemovalPolicy, Stack, Tags, aws_logs
from constructs import Construct


class LogGroupStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        log_group_name: str,
        retention: aws_logs.RetentionDays = aws_logs.RetentionDays.ONE_WEEK,
        **kwargs
    ):
        app_tag_name = kwargs.pop("app_tag_name", "app")
        app_tag_value = kwargs.pop("app_tag_value", "myapp")
        super().__init__(scope, id, **kwargs)

        # Create the CloudWatch Log Group
        # Automatically delete the log group when the stack is deleted
        self.log_group = aws_logs.LogGroup(
            self,
            "DjangoStackLogGroup",
            log_group_name=log_group_name,
            retention=retention,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Apply tags to the log group
        Tags.of(self.log_group).add(app_tag_name, app_tag_value)
