# clamda
command line tool for working with AWS lambda jobs more efficiently. It's designed to work quickly on the command line with AWS lambda jobs, especially where your workflow is something like:

* Write job in its own folder
* Upload to Lambda, Test
* Compare test results to expected, iterate

The process of doing this with AWS CLI or even with the AWS web UI is a bit laborious, so hopefully this tool makes it easier.

Setting up and Installation
===============

This library uses boto3, which uses system-wide configuration variables, so they're not embedded in the code at all and run nicely on the command line.

```
export AWS_SECRET_ACCESS_KEY=<YOUR SECRET KEY>
export AWS_ACCESS_KEY_ID=<YOUR ACCESS KEY>
export AWS_DEFAULT_REGION=us-east-1
```

To install the package, just 

```
pip install clamda
```

.clamda files
==================
When you run the tool, it will create a .clamda file in the directory that holds the json configuration for the job.

Running
===============
To run the tool, just go on the command line in a new directory and type:

```
clamda init
```

The tool will immediately ask you some questions to populate an AWS Lambda job such as the name of the job, the permissions role, and a the timeout for the job. It will create a stub job and upload it to your AWS lambda account (you can verify by logging into the UI)

To invoke a function, just call the invoke method with some json on the command line. You'll have to escape any special characters if you call it like this.

```
clamda invoke '{"asdf": "clamda"}'
```

and it will give you some output:
```
----- LOGS -------
START RequestId: 37ceb72c-b560-11e5-ab9c-c775d795d19a Version: $LATEST
END RequestId: 37ceb72c-b560-11e5-ab9c-c775d795d19a
REPORT RequestId: 37ceb72c-b560-11e5-ab9c-c775d795d19a  Duration: 17.53 ms  Billed Duration: 100 ms   Memory Size: 128 MB Max Memory Used: 9 MB

----- RESULT -----
{"asdf": "adab"}
```

Additionally, you can also call the invoke method by pushing in some json via command line STDIN. For instance, the below command will give you the same query output as above.

```
clamda invoke < text.txt
````

When you're ready to deploy some new code, simply run

```
clamda deploy
```

It will zip up your new code, upload the package to AWS Lambda. If you'd like to both deploy and invoke your function, you can call

Debugging & Working with Logs
====================
By default, when you create a new lambda job, amazon will create a corresponding CloudwatchLog entry for it where all your production logs will go. Working with their UI is a little painful, so clamda has some functions which will hopefully make this process easier to debug and find errors in live data:

To run a cloudwatch search for "error" in your logs:

```
clamda errors
```

If there are errors, it will print them to the terminal. If not, it will just report nothing.

Coming Soon
=====================

There are some important additional commands we need such as 

```
clamda test
```

So you can invoke your lambda function over assertions and datasets. This is coming in next version (january 2016). Also coming is 

```
clamda all
```

Which will both deploy and invoke your function over your test cases.

Committing
======================
Email Tom (thayden@gmail.com) if you have questions or submit a pull request to submit more. You might want to email me, first or submit an issue because this is a project under rapid development.

Thanks
======================
Mike Saunders (@saunders3000) is responsible for the clever name
