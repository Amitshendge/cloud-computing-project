from constructs import Construct
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_lambda as _lambda,
    aws_lambda_event_sources as event_sources,
    aws_s3 as s3,
    aws_apigateway as apigateway,
    CfnOutput,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins
)
import subprocess
import os

s3_name = "data-bucket-cc-project-app"
ROOT_DIR = os.path.abspath(os.curdir)

class AwsCdkUiStack(Stack):
    @staticmethod
    def npm_build(source_directory: str):
        result = subprocess.run(["npm", "run", "build"], cwd=source_directory, check=True)
        if result.returncode != 0:
            print("npm run build failed")
            raise Exception("npm run build failed")
        result = subprocess.run(["cp", "assets/photo.png", "dist/assets"], cwd=source_directory, check=True)
        print("React app built successfully.")

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        admin_role_ui = iam.Role(self, "admin_role_ui",
            role_name="Yolo_AdminRole_ui",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")]
        )
        self.npm_build(os.path.join(ROOT_DIR, 'UI'))

        ss3 = s3.Bucket(self, "DataBucketTextract",
            bucket_name=s3_name,
            
        )

        s3deploy.BucketDeployment(self, "DeployFiles",
            sources=[s3deploy.Source.asset("UI/dist")],
            destination_bucket=ss3,
            # destination_key_prefix="lambda_layers"
        )

        oai = cloudfront.OriginAccessIdentity(self, "MyOAI",
            comment="OAI for MyWebsiteBucket")

        ss3.add_to_resource_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[ss3.arn_for_objects("*")],
            principals=[iam.CanonicalUserPrincipal(oai.cloud_front_origin_access_identity_s3_canonical_user_id)]
        ))

        ss3.add_cors_rule(allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.POST, s3.HttpMethods.PUT, s3.HttpMethods.HEAD ], allowed_origins=["*"], allowed_headers=["*"])

        distribution = cloudfront.Distribution(self, "MyDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(ss3,
                    origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            ),
            default_root_object="index.html"
        )