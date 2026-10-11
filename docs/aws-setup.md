# ColdRescue — AWS Setup & M0 Foundation Guide

This document outlines the AWS environment, prerequisites, identity verification, CDK synthesis, least-privilege IAM permissions, deployment steps, and cleanup procedures for **Milestone 0 (Foundation)**.

**Safety rule:** Local tests and CDK synthesis do not deploy resources. Bootstrap, deployment, IAM changes, and teardown require explicit user authorization. Do not execute these operations without authorization.

---

## 1. Environment & Target Identity

| Parameter | Value |
|---|---|
| **AWS Account ID** | `<AWS_ACCOUNT_ID>` |
| **AWS Primary Region** | `ap-south-1` (Asia Pacific - Mumbai) |
| **IAM User** | `<REDACTED_IAM_USER>` |
| **CDK CLI Version** | `2.1145.0` (invoked via `npx aws-cdk`) |
| **Python CDK Library** | `aws-cdk-lib==2.145.0`, `constructs>=10.0.0,<11.0.0` |
| **Development Stack Name** | `ColdRescue-Foundation-development` |

---

## 2. Preflight Identity & CloudFormation Checks

Verify authentication and target region using the AWS CLI. These commands make AWS API requests but do not create infrastructure.

```powershell
# 1. Verify caller identity
$awsPath = "$env:LOCALAPPDATA\Programs\Amazon\AWSCLIV2\aws.exe"
& $awsPath sts get-caller-identity --output json

# 2. Check whether the CDKToolkit bootstrap stack exists in ap-south-1
& $awsPath cloudformation describe-stacks --stack-name CDKToolkit --region ap-south-1 --output json