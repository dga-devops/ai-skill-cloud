# Testing Strategy

> Source: AWS Prescriptive Guidance — "Best practices for using the AWS CDK in TypeScript to create IaC projects"

## Adopt a Test-Driven Development Approach

We recommend that you follow a test-driven development (TDD) approach with the AWS CDK. TDD is a software development approach where you develop test cases to specify and validate your code. In simple terms, first you create test cases for each functionality and if the test fails, then you write the new code to pass the test and make the code simple and bug-free.

You can use TDD to write the test case first. This helps you validate the infrastructure with different design constraints in terms of enforcing security policy for the resources and following a unique naming convention for the project. The standard approach to testing AWS CDK applications is to use the AWS CDK assertions module and popular test frameworks, such as Jest for TypeScript and JavaScript or pytest for Python.

## Two Categories of Tests

There are two categories of tests that you can write for your AWS CDK applications:

### Fine-Grained Assertions (Primary)

Use **fine-grained assertions** to test a specific aspect of the generated CloudFormation template, such as "this resource has this property with this value." These tests can detect regressions and are also useful when you're developing new features using TDD (write a test first, then make it pass by writing a correct implementation). Fine-grained assertions are the tests you'll write the most.

### Snapshot Tests

Use **snapshot tests** to test the synthesized CloudFormation template against a previously-stored baseline template. Snapshot tests make it possible to refactor freely, since you can be sure that the refactored code works exactly the same way as the original. If the changes were intentional, you can accept a new baseline for future tests. However, AWS CDK upgrades can also cause synthesized templates to change, so you can't rely only on snapshots to make sure your implementation is correct.

## Unit Test

This guide focuses on unit test integration for TypeScript specifically. To enable testing, make sure that your `package.json` file has the following libraries: `@types/jest`, `jest`, and `ts-jest` in `devDependencies`. To add these packages, run the `cdk init lib --language=typescript` command. After you run the preceding command, you see the following structure.

```
├── lib/
├── node_modules/
├── test/
├── .gitignore
├── .npmignore
├── jest.config.js
├── package-lock.json
├── package.json
├── README.md
└── tsconfig.json
```

The following code is an example of a `package.json` file that's enabled with the Jest library.

```json
{
  "scripts": {
    "build": "npm run lint && tsc",
    "watch": "tsc -w",
    "test": "jest"
  },
  "devDependencies": {
    "@types/jest": "27.5.2",
    "jest": "27.5.1",
    "ts-jest": "27.1.5"
  }
}
```

Under the **Test** folder, you can write the test case. The following example shows a test case for an AWS CodePipeline construct.

```typescript
import { Stack } from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import * as CodePipeline from 'aws-cdk-lib/aws-codepipeline';
import * as CodePipelineActions from 'aws-cdk-lib/aws-codepipeline-actions';
import { MyPipelineStack } from '../lib/my-pipeline-stack';

test('Pipeline Created with GitHub Source', () => {
  // ARRANGE
  const stack = new Stack();

  // ACT
  new MyPipelineStack(stack, 'MyTestStack');

  // ASSERT
  const template = Template.fromStack(stack);

  // Verify that the pipeline resource is created
  template.resourceCountIs('AWS::CodePipeline::Pipeline', 1);

  // Verify that the pipeline has the expected stages with GitHub source
  template.hasResourceProperties('AWS::CodePipeline::Pipeline', {
    Stages: [
      {
        Name: 'Source',
        Actions: [
          {
            Name: 'SourceAction',
            ActionTypeId: {
              Category: 'Source',
              Owner: 'ThirdParty',
              Provider: 'GitHub',
              Version: '1'
            },
            Configuration: {
              Owner: {
                'Fn::Join': [
                  '',
                  [
                    '{{resolve:secretsmanager:',
                    {
                      Ref: 'GitHubTokenSecret'
                    },
                    ':SecretString:owner}}'
                  ]
                ]
              },
              Repo: {
                'Fn::Join': [
                  '',
                  [
                    '{{resolve:secretsmanager:',
                    {
                      Ref: 'GitHubTokenSecret'
                    },
                    ':SecretString:repo}}'
                  ]
                ]
              },
              Branch: 'main',
              OAuthToken: {
                'Fn::Join': [
                  '',
                  [
                    '{{resolve:secretsmanager:',
                    {
                      Ref: 'GitHubTokenSecret'
                    },
                    ':SecretString:token}}'
                  ]
                ]
              }
            },
            OutputArtifacts: [
              {
                Name: 'SourceOutput'
              }
            ],
            RunOrder: 1
          }
        ]
      },
      {
        Name: 'Build',
        Actions: [
          {
            Name: 'BuildAction',
            ActionTypeId: {
              Category: 'Build',
              Owner: 'AWS',
              Provider: 'CodeBuild',
              Version: '1'
            },
            InputArtifacts: [
              {
                Name: 'SourceOutput'
              }
            ],
            OutputArtifacts: [
              {
                Name: 'BuildOutput'
              }
            ],
            RunOrder: 1
          }
        ]
      }
      // Add more stage checks as needed
    ]
  });

  // Verify that a GitHub token secret is created
  template.resourceCountIs('AWS::SecretsManager::Secret', 1);
});
```

To run a test, run the `npm run test` command in your project. The test returns the following results.

```
PASS  test/codepipeline-module.test.ts (5.972 s)
  # Code Pipeline Created (97 ms)
Test Suites: 1 passed, 1 total
Tests:       1 passed, 1 total
Snapshots:   0 total
Time:        6.142 s, estimated 9 s
```

## Integration Test

Integration tests for AWS CDK constructs can also be included by using an `integ-tests` module. An integration test should be defined as an AWS CDK application. There should be a one-to-one relationship between an integration test and an AWS CDK application. For more information, visit `integ-tests-alpha` module in the *AWS CDK API Reference*.

---

## Deployment Validation Workflow

Run these steps in order before every CDK deployment:

1. **`cdk synth`** — Confirm synthesis succeeds and cdk-nag reports no errors
2. **`npm run test`** — All assertion tests pass
3. **`cdk diff`** — Review IAM changes and resource replacements; stop and confirm with the user if unexpected replacements appear
4. **`cdk deploy`** — Apply the changes
5. **Verify runtime** — Confirm the deployed resource behaves correctly (e.g., check CloudWatch, hit an endpoint, run a smoke test)

> Never skip step 3 — if the diff shows a replacement on a stateful resource (RDS, DynamoDB, S3) it requires explicit user approval before deploying.
