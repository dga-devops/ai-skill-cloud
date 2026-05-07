# Security Scanning & Formatting

> Source: AWS Prescriptive Guidance — "Best practices for using the AWS CDK in TypeScript to create IaC projects"

## Scan for Security Vulnerabilities and Formatting Errors

Infrastructure as code (IaC) and automation have become essential for enterprises. With IaC being so robust, you have a large responsibility to manage security risks. Common IaC security risks can include the following:

- Over-permissive AWS Identity and Access Management (IAM) privileges
- Open security groups
- Unencrypted resources
- Access logs not turned on

## Security Approaches and Tools

We recommend that you implement the following security approaches:

### Vulnerability Detection in Development

Remediating vulnerabilities in production is expensive and time-consuming due to the complexity of developing and distributing software patches. Additionally, vulnerabilities in production carry the risk of exploitation. We recommend that you use code scanning on your IaC resources so that vulnerabilities can be detected and remediated prior to release into production.

### Compliance and Auto-Remediation

AWS Config offers AWS managed rules. These rules help you enforce compliance and enable you to attempt auto-remediation by using AWS Systems Manager automation. You can also create and associate custom automation documents by using AWS Config rules.

## Common Development Tools

The tools covered in this section help you to extend their built-in functionality with your own custom rules. We recommend that you align your custom rules with your organization's standards. Here are some common development tools to consider:

### cdk-nag

Use cdk-nag to validate that constructs within a given scope comply with a defined set of rules. You can also use cdk-nag for rule suppression and compliance reporting. The cdk-nag tool validates constructs by extending aspects in the AWS CDK. For more information, see *Manage application security and compliance with the AWS Cloud Development Kit (AWS CDK) and cdk-nag* in the AWS DevOps Blog.

### Checkov

Use the open-source tool Checkov to perform static analysis on your IaC environment. Checkov helps identify cloud misconfigurations by scanning your infrastructure code in Kubernetes, Terraform, or CloudFormation. You can use Checkov to get outputs in different formats, including JSON, JUnit XML, or CLI. Checkov can handle variables effectively by building a graph that shows dynamic code dependency.

### TFLint

Use TFLint to check for errors and deprecated syntax and to help you enforce best practices. Note that TFLint may not validate provider-specific issues.

### Amazon Q Developer

Use Amazon Q Developer to perform security scans. When used in an integrated development environment (IDE), Amazon Q Developer provides AI-powered software development assistance. It can chat about code, provide inline code completions, generate net new code, scan your code for security vulnerabilities, and make code upgrades and improvements.

## Documentation

### Why Code Documentation Is Required for AWS CDK Constructs

AWS CDK common constructs are created by multiple teams in an organization and shared across different teams for consumption. Good documentation helps the consumers of the construct library easily integrate constructs and build their infrastructure with minimum effort. Keeping all documents in sync is a big task. We recommend that you maintain the document inside the code, which will be extracted using the TypeDoc library.

### Using TypeDoc with the AWS Construct Library

TypeDoc is a document generator for TypeScript. You can use TypeDoc to read your TypeScript source files, parse the comments in those files, and then generate a static site that contains documentation for your code.

The following code shows you how to integrate TypeDoc with the AWS Construct Library, and then add the following packages in your `package.json` file in `devDependencies`.

```json
{
  "devDependencies": {
    "typedoc-plugin-markdown": "^3.11.7",
    "typescript": "~3.9.7"
  }
}
```

To add `typedoc.json` in the CDK library folder, use the following code.

```json
{
  "$schema": "https://typedoc.org/schema.json",
  "entryPoints": ["./lib"]
}
```

To generate the README files, run the `npx typedoc` command in the root directory of the AWS CDK construct library project.

## Version Control and Release

### Version Control for the AWS CDK

AWS CDK common constructs can be created by multiple teams and shared across an organization for consumption. Typically, developers release new features or bug fixes in their common AWS CDK constructs. These constructs are used by AWS CDK applications or any other existing AWS CDK constructs as part of a dependency. For this reason, it's crucial that developers update and release their construct with proper semantic versions independently. Downstream AWS CDK applications or other AWS CDK constructs can update their dependency to use the newly released AWS CDK construct version.

### Semantic Versioning (Semver)

Semantic versioning (Semver) is a set of rules, or method, for providing unique software numbers to computer software. Versions are defined as follows:

- A **MAJOR** version consists of incompatible API changes or a breaking change.
- A **MINOR** version consists of functionality that's added in a backwards-compatible manner.
- A **PATCH** version consists of backwards-compatible bug fixes.

### Repository and Packaging for AWS CDK Constructs

As AWS CDK constructs are developed by different teams and are used by multiple AWS CDK applications, you can use a separate repository for each AWS CDK construct. This also can help you enforce access control. Each repository could contain all the source code related to the same AWS CDK construct along with all of its dependencies. By keeping a single application (that is, an AWS CDK construct) in a single repository, you can decrease the scope of impact of changes during deployment.

The AWS CDK not only generates CloudFormation templates for deploying infrastructure, but it also bundles runtime assets like Lambda functions and Docker images and deploys them alongside your infrastructure. It's not only possible to combine the code that defines your infrastructure and the code that implements your runtime logic into a single construct — it's a best practice. These two kinds of code don't need to live in separate repositories or even in separate packages.

To consume packages across repository boundaries, you must have a private package repository — similar to npm, PyPi, or Maven Central, but internal to your organization. You must also have a release process that builds, tests, and publishes the package to the private package repository. You can create private repositories, such as PyPi server, by using a local virtual machine (VM) or Amazon S3. When you design or create a private package registry, it's crucial to consider the risk of service disruption due to high availability and scalability. A serverless managed service that's hosted in the cloud to store packages can greatly decrease the maintenance overhead. For example, you can use AWS CodeArtifact to host packages for most popular programming languages. You can also use CodeArtifact to set external repository connections and replicate them within CodeArtifact.

### Construct Releasing for the AWS CDK

We recommend that you create your own automated pipeline to build and release new AWS CDK construct versions. If you put a proper pull request approval process in place, then once you commit and push your source code into the main branch of the repository, the pipeline can build and create a release candidate version. That version can be pushed to CodeArtifact and tested before releasing the production-ready version. Optionally, you can test your new AWS CDK construct version locally before merging the code with the main branch. This causes the pipeline to release the production-ready version. Take into consideration that shared constructs and packages must be tested independently of the consuming application, as if they were being released to the public.

You can use the following sample commands to build, test, and publish npm packages. First, sign in to the artifact repository by running the following command.

```bash
aws codeartifact login --tool npm --domain <Domain Name> --domain-owner $(aws sts get-caller-identity --output text --query 'Account') \
--repository <Repository Name> --region <AWS Region Name>
```

Then, complete the following steps:

1. Install the required packages based on the `package.json` file: `npm install`
2. Create the release candidate version: `npm version prerelease --preid rc`
3. Build the npm package: `npm run build`
4. Test the npm package: `npm run test`
5. Publish the npm package: `npm publish`

## Enforce Library Version Management

Lifecycle management is a significant challenge when you're maintaining AWS CDK code bases. For example, assume that you start an AWS CDK project with version 1.97 and then version 1.169 becomes available later on. Version 1.169 offers new features and bug fixes, but you have deployed your infrastructure by using the old version. Now, updating the constructs becomes challenging as this gap increases because of the breaking changes that could be introduced in new versions. This can be a challenge if you have many resources in your environment. The pattern introduced in this section can help you manage your AWS CDK library version using automation. Here's the workflow of this pattern:

1. When you launch a new CodeArtifact Service Catalog product, the AWS CDK library versions and its dependencies are stored in the `package.json` file.
2. You deploy a common pipeline that keeps track of all the repositories so that you can apply automatic upgrades to them if there are no breaking changes.
3. An AWS CodeBuild stage checks for the dependency tree and looks for the breaking changes.
4. The pipeline creates a feature branch and then runs `cdk synth` with the new version to confirm there are no errors.
5. The new version is deployed in the test environment and finally runs an integration test to make sure the deployment is healthy.
6. You can use two Amazon Simple Queue Service (Amazon SQS) queues to keep track of the stacks. Users can review the stacks manually in the exception queue and address breaking changes. Items that pass the integration test are allowed to be merged and released.

---

## RemovalPolicy

Always set `removalPolicy` explicitly on every stateful resource (S3, RDS, DynamoDB, EFS, etc.). Never rely on CDK's implicit default:

| Environment | Policy | Reason |
|---|---|---|
| `sandbox`, `dev` | `RemovalPolicy.DESTROY` | Fast teardown, no production data |
| `uat`, `preprod`, `prod` | `RemovalPolicy.RETAIN` | Prevent accidental data loss |

Drive the value from config:

```typescript
removalPolicy: config.env.envName === 'prod'
  ? RemovalPolicy.RETAIN
  : RemovalPolicy.DESTROY
```

---

## IAM: Use Grant Helpers

Prefer L2 grant methods over manually constructed `PolicyStatement` objects — intent is clearer and least-privilege by design:

```typescript
// ✅ Correct
bucket.grantRead(lambdaFunction);
table.grantReadWriteData(lambdaFunction);
queue.grantSendMessages(lambdaFunction);

// ❌ Avoid — easy to over-permission, hard to review
lambdaFunction.addToRolePolicy(new iam.PolicyStatement({
  actions: ['s3:*'],
  resources: ['*'],
}));
```

Use `PolicyStatement` directly only when no grant helper exists for the required permission.
