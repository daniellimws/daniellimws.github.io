---
layout: post
type: note
title: flaws.cloud notes
alias: flAWS
---

## Level 1

### 1. Identify whether a site is hosted as an S3 bucket

Use `dig` to do a DNS lookup on the domain.

```
❯ dig +nocmd flaws.cloud +answer +multiline
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 54467
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;flaws.cloud.		IN A

;; ANSWER SECTION:
flaws.cloud.		4 IN A	52.218.251.26

;; Query time: 8 msec
;; SERVER: 8.8.8.8#53(8.8.8.8)
;; WHEN: Mon Jan 11 10:18:48 +08 2021
;; MSG SIZE  rcvd: 45
```

Visiting [52.218.251.26](http://52.218.251.26) in the browser brings me to https://aws.amazon.com/s3/. Or use `curl` to see the redirected URL.

```
❯ curl -Ls -o /dev/null -w %{url_effective} 52.218.251.26

https://aws.amazon.com/s3/
```

Or, use `nslookup`, to realize that it is indeed a s3 bucket, hosted in the AWS region us-west-2.

```
❯ nslookup 52.218.251.26
Server:		8.8.8.8
Address:	8.8.8.8#53

Non-authoritative answer:
26.251.218.52.in-addr.arpa	name = s3-website-us-west-2.amazonaws.com.

Authoritative answers can be found from:


```

> Side note: All S3 buckets, when configured for web hosting, are given an AWS domain you can use to browse to it without setting up your own DNS. In this case, flaws.cloud can also be visited by going to http://flaws.cloud.s3-website-us-west-2.amazonaws.com/

### 2. Attempt to browse the bucket

```
❯ aws s3 ls s3://flaws.cloud --no-sign-request --region us-west-2
2017-03-14 11:00:38       2575 hint1.html
2017-03-03 12:05:17       1707 hint2.html
2017-03-03 12:05:11       1101 hint3.html
2020-05-23 02:16:45       3162 index.html
2018-07-11 00:47:16      15979 logo.png
2017-02-27 09:59:28         46 robots.txt
2017-02-27 09:59:30       1051 secret-dd02c7c.html
```

The `--no-sign-request` argument works as follows:

```plaintext
--no-sign-request (boolean)

Do not sign requests. Credentials will not be loaded if this argument is provided.
```

Due to bad permission configurations, I can list the bucket without any credentials.

If I don't know the region, I can either try them one by one, or use [cyberduck](https://cyberduck.io/?l=en) to browse it, which will figure out the region automatically.

> You can also just visit http://flaws.cloud.s3.amazonaws.com/ which lists the files due to the permissions issues on this bucket.

## Level 2

Trying to list the bucket doesn't work here.

```
❯ aws s3 ls s3://level2-c8b217a33fcf1f839f6f1f73a00a9ae7.flaws.cloud --no-sign-request --region us-west-2

An error occurred (AccessDenied) when calling the ListObjectsV2 operation: Access Denied
```