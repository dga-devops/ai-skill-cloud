# Create or Extend Constructs

> Source: AWS Prescriptive Guidance — "Best practices for using the AWS CDK in TypeScript to create IaC projects"
>
> **Project preference:** Always use L2 constructs — do not use L3 (patterns) unless there is a clear, justified reason.

## What a Construct Is

A construct is the basic building block of an AWS CDK application. A construct can represent a single AWS resource, such as an Amazon Simple Storage Service (Amazon S3) bucket, or it can be a higher-level abstraction consisting of multiple AWS related resources. The components of a construct can include a worker queue with its associated compute capacity, or a scheduled job with monitoring resources and a dashboard. The AWS CDK includes a collection of constructs called the AWS Construct Library. The library contains constructs for every AWS service. You can use the Construct Hub to discover additional constructs from AWS, third parties, and the open-source AWS CDK community.

## What the Different Types of Constructs Are

There are three different types of constructs for the AWS CDK:

### L1 Constructs

Layer 1, or L1, constructs are exactly the resources defined by CloudFormation — no more, no less. You must provide the resources required for configuration yourself. These L1 constructs are very basic and must be manually configured. L1 constructs have a `Cfn` prefix and correspond directly to CloudFormation specifications. New AWS services are supported in AWS CDK as soon as CloudFormation has support for these services. `CfnBucket` is a good example of an L1 construct. This class represents an S3 bucket where you must explicitly configure all the properties. **We recommend that you only use an L1 construct if you can't find the L2 construct for it.**

### L2 Constructs (Preferred ✅)

Layer 2, or L2, constructs have common boilerplate code and glue logic. These constructs come with convenient defaults and reduce the amount of knowledge you need to know about them. L2 constructs use intent-based APIs to construct your resources and typically encapsulate their corresponding L1 modules. A good example of an L2 construct is `Bucket`. This class creates an S3 bucket with default properties and methods such as `bucket.addLifeCycleRule()`, which adds a lifecycle rule to the bucket.

### L3 Constructs (Not Used in This Project ⛔)

A layer 3, or L3, construct is called a *pattern*. L3 constructs are designed to help you complete common tasks in AWS, often involving multiple kinds of resources. These are even more specific and opinionated than L2 constructs and serve a specific use case. For example, the `aws-ecs-patterns.ApplicationLoadBalancedFargateService` construct represents an architecture that includes an AWS Fargate container cluster that uses an Application Load Balancer.

> **⚠️ Project Rule:** Do not use L3 constructs in this project. Compose L2 constructs manually instead for finer-grained configuration control.

As construct levels get higher, more assumptions are made as to how these constructs are going to be used. This allows you to provide interfaces with more effective defaults for highly specific use cases.

## Construct Hierarchy Summary

| Level | Prefix / Style | Use When | Project Policy |
|-------|---------------|----------|----------------|
| L1 | `Cfn*` | No L2 available | Use only when necessary |
| L2 | Direct class name (e.g. `Bucket`) | Whenever an L2 exists | **✅ Always preferred** |
| L3 | Pattern constructs | — | **⛔ Do not use** |

## How to Create Your Own Construct

To define your own construct, you must follow a specific approach. This is because all constructs extend the `Construct` class. The `Construct` class is the building block of the construct tree. Constructs are implemented in classes that extend the `Construct` base class. All constructs take three parameters when they are initialized:

- **Scope** – A construct's parent or owner, either a stack or another construct, which determines its place in the construct tree. You usually must pass `this` (or `self` in Python), which represents the current object, for the scope.
- **id** – An identifier that must be unique within this scope. The identifier serves as a namespace for everything that's defined within the current construct and is used to allocate unique identities, such as resource names and CloudFormation logical IDs.
- **Props** – A set of properties that define the construct's initial configuration.

The following example shows how to define a construct.

```typescript
import { Construct } from 'constructs';

export interface CustomProps {
  // List all the properties
  Name: string;
}

export class MyConstruct extends Construct {
  constructor(scope: Construct, id: string, props: CustomProps) {
    super(scope, id);

    // TODO
  }
}
```

## Create or Extend an L2 Construct

An L2 construct represents a "cloud component" and encapsulates everything that CloudFormation must have to create the component. An L2 construct can contain one or more AWS resources, and you're free to customize the construct yourself. The advantage of creating or extending an L2 construct is that you can reuse the components in CloudFormation stacks without redefining the code. You can simply import the construct as a class.

When there's an "is a" relationship to an existing construct you can extend an existing construct to add additional default features. It's a best practice to reuse the properties of the existing L2 construct. You can overwrite properties by modifying the properties directly in the constructor.

The following example shows how to align with best practices and extend an existing L2 construct called `s3.Bucket`. The extension establishes default properties, such as `versioned`, `publicReadAccess`, `blockPublicAccess`, to make sure that all the objects (in this example, S3 buckets) created from this new construct will always have these default values set.

```typescript
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

export class MySecureBucket extends s3.Bucket {
  constructor(scope: Construct, id: string, props?: s3.BucketProps) {
    super(scope, id, {
      ...props,
      versioned: true,
      publicReadAccess: false,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL
    });
  }
}
```

## Escape Hatch

You can use an escape hatch in the AWS CDK to go up an abstraction level so that you can access the lower level of constructs. Escape hatches are used to extend the construct for features which are not exposed with the current version of AWS but available in CloudFormation.

We recommend that you use an escape hatch in the following scenarios:

- An AWS service feature is available through CloudFormation, but there are no `Construct` constructs for it.
- An AWS service feature is available through CloudFormation and there are `Construct` constructs for the service, but these don't yet expose the feature. Because `Construct` constructs are developed "by hand," they may sometimes lag behind the CloudFormation resource constructs.

The following example code shows a common use case for using an escape hatch. In this example, the functionality that's not yet implemented in the higher-level construct is for adding `httpPutResponseHopLimit` for autoscaling `LaunchConfiguration`.

```typescript
const launchConfig = autoscaling.onDemandASG.node.findChild("LaunchConfig") as
  CfnLaunchConfiguration;
  launchConfig.metadataOptions = {
    httpPutResponseHopLimit: autoscalingConfig.httpPutResponseHopLimit ||
    2
  }
```

The preceding code example shows the following workflow:

1. You define your `AutoScalingGroup` by using an L2 construct. The L2 construct doesn't support updating the `httpPutResponseHopLimit`, so you must use an escape hatch.
2. You use the `node.findChild()` method to locate the specific `LaunchConfig` child of the L2 `AutoScalingGroup` construct and cast it as the `CfnLaunchConfiguration` resource.
3. You can now set the `launchConfig.metadataOptions` property on the L1 `CfnLaunchConfiguration`.

## Preserve Implicit Dependencies When Overriding References

When you pass a construct to an L2 prop (e.g. `taskDefinition: taskDef`), CDK renders a `Ref` / `Fn::GetAtt` in the template. CloudFormation reads that token and creates an **implicit `DependsOn`** — the referenced resource is always provisioned first.

`addPropertyOverride()` / `addOverride()` replace the rendered value with a raw literal. The `Ref` disappears — **and the implicit dependency disappears with it.** CloudFormation is then free to order those resources independently, producing non-deterministic deploy failures where a resource is created before the thing it depends on exists.

> **⚠️ Rule:** Whenever an override replaces a property that normally carries a cross-resource `Ref` / `Fn::GetAtt`, restore the ordering manually with `<construct>.node.addDependency(<target>)`.

**Symptom:** Intermittent `cdk deploy` failures such as `TaskDefinition not found`, `... does not exist`, or `... not found` on the overridden resource. Typically *passes on the first environment* (CloudFormation happened to create the dependency first) and *fails on the next* with identical code — a classic race condition.

**Common case — ECS Service referencing a TaskDefinition by family name** (so the CI/CD pipeline owns the running revision, not CDK):

```typescript
const service = new ecs.FargateService(this, `${name}Service`, {
  cluster,
  taskDefinition: taskDef,   // CDK renders a Ref → implicit DependsOn on taskDef
  // ...
});

// Override to a raw family name so CI/CD controls the running revision.
// ⚠️ This deletes the Ref — and the implicit dependency along with it.
const cfnService = service.node.defaultChild as ecs.CfnService;
cfnService.addPropertyOverride('TaskDefinition', family);

// ✅ Restore the ordering: TaskDefinition is now always registered before the Service.
service.node.addDependency(taskDef);
```

## ECS Service: Fast-Fail Deployments

Enable the deployment circuit breaker on ECS services so a bad deployment rolls back in minutes instead of hanging:

```typescript
const service = new ecs.FargateService(this, `${name}Service`, {
  cluster,
  taskDefinition: taskDef,
  circuitBreaker: { rollback: true },
  // ...
});
```

Without it, if a task can't pull its image or never reaches a healthy state, CloudFormation waits for the full service stabilization timeout (~3 hours) before failing the stack. cdk-nag already flags the missing setting via `@aws-cdk/aws-ecs:shouldUseCircuitBreaker`.

## ALB ↔ ECS: Target Registration

Because we compose L2 constructs by hand (no `ApplicationLoadBalancedFargateService` L3 pattern), the service is **not** wired to the load balancer automatically. Creating a target group and a listener rule is not enough — the service must register its tasks as targets.

> **⚠️ Rule:** When an ECS/Fargate service sits behind an ALB, always register it as a target via `service.attachToApplicationTargetGroup(targetGroup)` (or `targetGroup.addTarget(service)`). A target group + listener rule alone leaves the target group empty.

**Symptom:** `cdk synth`/`cdk deploy` both succeed and the task reaches `RUNNING`, but the ALB returns **HTTP 503** for every request because the target group has no registered targets. Like the `DependsOn` race above, this is a "passes synth, fails at runtime" pitfall — the gap is invisible in the template.

```typescript
const service = new ecs.FargateService(this, `${name}Service`, {
  cluster,
  taskDefinition: taskDef,
  circuitBreaker: { rollback: true },
  // ...
});

const targetGroup = new elbv2.ApplicationTargetGroup(this, `${name}Tg`, {
  vpc,
  port: containerPort,
  protocol: elbv2.ApplicationProtocol.HTTP,
  targetType: elbv2.TargetType.IP,
  // health check, name from config, etc.
});

listener.addTargetGroups(`${name}Rule`, {
  targetGroups: [targetGroup],
  // conditions, priority, ...
});

// ✅ Without this the target group stays empty → ALB returns 503 despite RUNNING tasks.
service.attachToApplicationTargetGroup(targetGroup);
```

## ECS: ECR Image Pull Permission

For container images stored in ECR, use `ecs.ContainerImage.fromEcrRepository(repo, tag)`. This grants the task **execution role** pull permission on that repository automatically. Referencing the same image by its registry URI with `ecs.ContainerImage.fromRegistry('<account>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>')` does **not** grant any permission — `fromRegistry` is for public/external registries and assumes the role can already pull.

> **⚠️ Rule:** Pull ECR images with `fromEcrRepository(repo, tag)`, not `fromRegistry(<ECR URI>)`. The former wires up the execution-role pull grant; the latter leaves it missing.

**Symptom:** The task fails to start with `CannotPullContainerError` (access denied on the ECR repository), even though the image and tag exist.

```typescript
import * as ecr from 'aws-cdk-lib/aws-ecr';

const repo = ecr.Repository.fromRepositoryName(this, 'Repo', repoName);

taskDef.addContainer(`${name}Container`, {
  // ✅ Grants the execution role ecr:GetDownloadUrlForLayer / BatchGetImage automatically.
  image: ecs.ContainerImage.fromEcrRepository(repo, imageTag),
  // ❌ ecs.ContainerImage.fromRegistry(ecrUri) → no grant → CannotPullContainerError
  // ...
});
```

## Custom Resources

You can use custom resources to write custom provisioning logic in templates that CloudFormation runs whenever you create, update (if you changed the custom resource), or delete stacks. For example, you can use a custom resource if you want to include resources that aren't available in the AWS CDK. That way you can still manage all your related resources in a single stack.

Building a custom resource involves writing a Lambda function that responds to a resource's CREATE, UPDATE, and DELETE lifecycle events. If your custom resource must make only a single API call, consider using the `AwsCustomResource` construct. This makes it possible to perform arbitrary SDK calls during a CloudFormation deployment. Otherwise, we suggest that you write your own Lambda function to perform the work that you must get done.

The following example shows how to create a custom resource class to initiate a Lambda function and send CloudFormation a success or fail signal.

```typescript
import cdk = require('aws-cdk-lib');
import customResources = require('aws-cdk-lib/custom-resources');
import lambda = require('aws-cdk-lib/aws-lambda');
import { Construct } from 'constructs';
import fs = require('fs');

export interface MyCustomResourceProps {
  /**
   * Message to echo
   */
  message: string;
}

export class MyCustomResource extends Construct {
  public readonly response: string;

  constructor(scope: Construct, id: string, props: MyCustomResourceProps) {
    super(scope, id);

    const fn = new lambda.SingletonFunction(this, 'Singleton', {
      uuid: 'f7d4f730-4ee1-11e8-9c2d-fa7ae01bbebc',
      code: new lambda.InlineCode(fs.readFileSync('custom-resource-handler.py',
        { encoding: 'utf-8' })),
      handler: 'index.main',
      timeout: cdk.Duration.seconds(300),
      runtime: lambda.Runtime.PYTHON_3_6,
    });

    const provider = new customResources.Provider(this, 'Provider', {
      onEventHandler: fn,
    });

    const resource = new cdk.CustomResource(this, 'Resource', {
      serviceToken: provider.serviceToken,
      properties: props,
    });

    this.response = resource.getAtt('Response').toString();
  }
}
```

The following example shows the main logic of the custom resource (Python handler).

```python
def main(event, context):
    import logging as log
    import cfnresponse
    log.getLogger().setLevel(log.INFO)

    # This needs to change if there are to be multiple resources in the same stack
    physical_id = 'TheOnlyCustomResource'

    try:
        log.info('Input event: %s', event)

        # Check if this is a Create and we're failing Creates
        if event['RequestType'] == 'Create' and
            event['ResourceProperties'].get('FailCreate', False):
            raise RuntimeError('Create failure requested')

        # Do the thing
        message = event['ResourceProperties']['Message']
        attributes = {
            'Response': 'You said "%s"' % message
        }

        cfnresponse.send(event, context, cfnresponse.SUCCESS, attributes, physical_id)
    except Exception as e:
        log.exception(e)
        # cfnresponse's error message is always "see CloudWatch"
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_id)
```

The following example shows how the AWS CDK stack calls the custom resource.

```typescript
import cdk = require('aws-cdk-lib');
import { MyCustomResource } from './my-custom-resource';

/**
 * A stack that sets up MyCustomResource and shows how to get an attribute from it
 */
class MyStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const resource = new MyCustomResource(this, 'DemoResource', {
      message: 'CustomResource says hello',
    });

    // Publish the custom resource output
    new cdk.CfnOutput(this, 'ResponseMessage', {
      description: 'The message that came back from the Custom Resource',
      value: resource.response
    });
  }
}

const app = new cdk.App();
new MyStack(app, 'CustomResourceDemoStack');
app.synth();
```
