import aws_cdk as core
import aws_cdk.assertions as assertions

from yeastregulatorydbstack.yeastregulatorydbstack_stack import (
    YeastregulatorydbstackStack,
)


# example tests. To run these tests, uncomment this file along with the example
# resource in yeastregulatorydbstack/yeastregulatorydbstack_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = YeastregulatorydbstackStack(app, "yeastregulatorydbstack")
    template = assertions.Template.from_stack(stack)


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
