# bada
command line tool for working with AWS lambda jobs more efficiently. It's designed to work quickly on the command line with AWS lambda jobs, especially where your workflow is something like:

* Write job
* Upload to Lambda, Test
* Compare test results to expected, iterate

The process of doing this with AWS CLI or even with the AWS web UI is a bit laborious, so hopefully this tool makes it easier.

Setting up
===============

This library uses boto3, which uses system-wide configuration variables, so they're not embedded in the code at all and run nicely on the command line.

```
export AWS_SECRET_ACCESS_KEY=<YOUR SECRET KEY>
export AWS_ACCESS_KEY_ID=<YOUR ACCESS KEY>
export AWS_DEFAULT_REGION=us-east-1
```

