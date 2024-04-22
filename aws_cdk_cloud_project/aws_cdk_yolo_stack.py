from constructs import Construct
import json
import os
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as event_sources,
    aws_s3 as s3,
    aws_apigateway as apigateway,
    CfnOutput,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_ssm as ssm
)
s3_name = "data-bucket-cc-project-app"
ROOT_DIR = os.path.abspath(os.curdir)

class AwsCdkYoloStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        admin_role = iam.Role(self, "AdminRole",
            role_name="Yolo_AdminRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")]
        )

        opencv_layer = _lambda.LayerVersion(self, "opencv_lambda_layer",
            code=_lambda.Code.from_asset("lambdas/lambda_layers"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description="OpenCV layer"
        )

        image_edit_cv2_lambda = _lambda.Function(self, "image_edit_cv2",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/image_edit_cv2"),
            function_name="image_edit_cv2",
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "BUCKET_NAME": s3_name
            },
            role=admin_role,  # Add admin_role to the lambda function
            layers=[
                    _lambda.LayerVersion.from_layer_version_arn(self, "numpy-layer", "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p39-numpy:17"),
                    _lambda.LayerVersion.from_layer_version_arn(self, "Klayers-p39-pillow", "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p39-pillow:1")
                    ]
                )
        
        generate_presigned_download_lambda = _lambda.Function(self, "generate_presigned_download",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/generate_presigned_download"),
            function_name="generate_presigned_download",
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "BUCKET_NAME": s3_name
            },
            role=admin_role,  # Add admin_role to the lambda function
        )
        
        generate_presigned_upload_lambda = _lambda.Function(self, "generate_presigned_upload",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/generate_presigned_upload"),
            function_name="generate_presigned_upload",
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "BUCKET_NAME": s3_name
            },
            role=admin_role,  # Add admin_role to the lambda function
        )

        yolo_dockerFunc = _lambda.DockerImageFunction(self, "yolo_dockerFunc",
            code=_lambda.DockerImageCode.from_image_asset("./yolo_image"),
            memory_size=2024,
            timeout=Duration.seconds(900),
            architecture=_lambda.Architecture.ARM_64,
            function_name="yolo_dockerFunc",
            role=admin_role,  # Add admin_role to the lambda function
            environment={
                "BUCKET_NAME": s3_name
            },
        )

        yolo_dockerFunc_function_url = yolo_dockerFunc.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_methods=[_lambda.HttpMethod.ALL],
                allowed_headers=["*"],
                allowed_origins=["*"]),
        )

        api = apigateway.RestApi(self, "application-api",
                  rest_api_name="application-api",
                  description="This service serves widgets.",
                  default_cors_preflight_options={
                      "allow_origins": apigateway.Cors.ALL_ORIGINS,
                      "allow_methods": apigateway.Cors.ALL_METHODS,
                      "allow_headers": apigateway.Cors.DEFAULT_HEADERS
                  })

        image_edit_cv2_lambda_integration = apigateway.LambdaIntegration(image_edit_cv2_lambda,
                request_templates={"application/json": '{ "statusCode": "200" }'})

        generate_presigned_download_lambda_integration = apigateway.LambdaIntegration(generate_presigned_download_lambda,
                request_templates={"application/json": '{ "statusCode": "200" }'})
        
        generate_presigned_upload_lambda_integration = apigateway.LambdaIntegration(generate_presigned_upload_lambda,
                request_templates={"application/json": '{ "statusCode": "200" }'})

        api.root.add_resource("image_edit_cv2").add_method("POST", image_edit_cv2_lambda_integration)
        api.root.add_resource("generate_presigned_download").add_method("GET", generate_presigned_download_lambda_integration)
        api.root.add_resource("generate_presigned_upload").add_method("GET", generate_presigned_upload_lambda_integration)

        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "yolo_dockerFunc_function_url", value=yolo_dockerFunc_function_url.url)