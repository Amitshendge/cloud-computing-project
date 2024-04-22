#!/usr/bin/env python3

import aws_cdk as cdk

from aws_cdk_cloud_project.aws_cdk_yolo_stack import AwsCdkYoloStack
from aws_cdk_cloud_project.aws_cdk_ui_stack import AwsCdkUiStack

app = cdk.App()
yolo_stack = AwsCdkYoloStack(app, "AwsCdkYoloStack", env={'region': 'us-east-1'})
ui_stack = AwsCdkUiStack(app, "AwsCdkUiStack", env={'region': 'us-east-1'})

ui_stack.add_dependency(yolo_stack)

app.synth()
