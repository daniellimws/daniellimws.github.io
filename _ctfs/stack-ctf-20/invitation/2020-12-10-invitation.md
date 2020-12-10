---
layout: post
title: An invitation (re)
ctf: STACK The Flags CTF 2020
permalink: /stack-ctf-20/an-invitation
---

> We want you to be a member of the Cyber Defense Group! Your invitation has been encoded to avoid being detected by COViD's sensors. Decipher the invitation and join in the fight!
>
> [Challenge files][challenge-files]

In this challenge, we are given 3 files: **index.html**, **invite.js**, **jquery-led.js**.

When opening **index.html** in the browser, nothing shows up. I opened the Chrome Dev Tools and looked at the console. The following error message was given.

```js
Uncaught ReferenceError: gl is not defined
    at invite.js:2
```

Not sure what is going wrong, but I suppose I will need to look more into **invite.js** to know the problem.

### Source files given

**index.html** is straightforward, it imports the relevant stylesheets and scripts, and places a `<canvas>` element in the page.

```html
<!doctype html>
<html lang="en">
    <head>
        <!-- Required meta tags -->
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

        <!-- Bootstrap CSS -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">

        <title>Hello, world!</title>
    </head>
    <body>
        <div class="container">
            <br />
            <div class="custom1"></div>
            <div class="custom2"></div>
            <div class="custom3"></div>
            <canvas class="GG" id="glglglgl" width="1" height="1" shade="e" type="l"></canvas>
            <br />
        </div>
        <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ho+j7jyWK8fNQe+A12Hb8AhRq26LrZ/JpcUGGOn+Y7RsweNrtN/tE3MoK7ZeZDyx" crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/raphael/2.2.7/raphael.min.js"></script>
        <script src="jquery-led.js"></script>
        <script src="invite.js"></script>
    </body>
</html>
```

**jquery-led.js** is slightly big, with 300 lines. Scrolling through the file, it seems to contain code that is related to showing a LED panel drawn onto the webpage.

**invite.js** contains one line of obfuscated javascript code. After splitting the code into multiple lines, the code structure looks something like the following.

```js
var _0x3f3a=["\x2E\x47","\x71\x75\x65\x72\x79\x53\x65\x6C\x65\x63\x74\x6F\x72","\x77\x65\x62\x67\x6C",...   // truncated
try { /* something */ } catch (err) { /* something */ }
// some more code
```

As shown above, there is an error in **invite.js**, so my current goal is to deobfuscate this code to know what is happening.

### Better strings
It is clear that `_0x3f3a` contains strings in their hexadecimal format, which can be more easily read if we convert them to their ASCII representation. For example, `\x2E\x47` is equal to `.G`. The easiest way to do so is by pasting the whole array into the console of the browser dev tools.

![console][console]

I replaced the array in the original code with the one with ASCII characters above. Then, I used *search and replace* to replace `_0x3f3a` with `strings` to improve readability.

The code now looks like this.

```js
var strings = [/* the strings */];
try {
canvas= document[strings[1]](strings[0]);
gl= canvas[strings[3]](strings[2]);
gl[strings[4]](0.0,0.0,0.0,1.0);
gl[strings[5]](gl.COLOR_BUFFER_BIT);
shade= canvas[strings[7]](strings[6]);
ctype= canvas[strings[7]](strings[8]);
cid= canvas[strings[7]](strings[10])[strings[9]](5,7);
gl[strings[11]]= window[shade+ cid+ ctype]
} catch (err);

// more code
```

To make the code actually readable, I need to replace all instances of `strings[..]` to the actual strings from the array.
I wrote a simple Python script to do this.

```py
strings=[".GG","querySelector","webgl","getContext","clearColor","clear","shade","getAttribute","type","slice","id","KG","||||||function|var||hhh||||for|charCodeAt|if|length|eee||uuu||mmm|||custom|fromCharCode|String|vvv||ggg|location|catLED|type||color||rounded|font_type|background_color|e0e0e0|size|return|zzz|FF0000|value|seed|yyy|rrr||ooo|slice|ttt|false|window|else|you|iii|let|YOU||compare|0xff|||23|re|hostname|console|||57|protocol|file|54|log|max|Math|98|requestAnimationFrame|true|0BB|00|88|09|0FZ|02|0D|06HD|03S|31|get|new|Image|Object|defineProperty|id|unescape|invited|2000|pathname|const|ech||setTimeout|WANT|WE|custom3|custom2|INVITED|RE|custom1|debugger|1000|invite|the|accepting|alert|Thank|indexOf|go|118|3V3jYanBpfDq5QAb7OMCcT|leaHVWaWLfhj4|atob","toString","replace","x=[0,0,0];1C Y=(a,b)=>{V s=\'\';d(V i=0;i<1e.1d(a.g,b.g);i++){s+=q.p((a.e(i)||0)^(b.e(i)||0))}F s};f(u.19==\'1a:\'){x[0]=12}S{x[0]=18}f(Y(R.u.14,\"T\'13 1z!!!\")==1y(\"%1E%1j%1q%17%1p%1o%1n%1m%1l%1i@M\")){x[1]=1k}S{x[1]=1r}6 K(){7 j=Q;7 G=1t 1u();1v.1w(G,\'1x\',{1s:6(){j=1h;x[2]=1b}});1g(6 X(){j=Q;15.1c(\"%c\",G);f(!j){x[2]=1f}})};K();6 N(J){7 m=Z;7 a=11;7 c=17;7 z=J||3;F 6(){z=(a*z+c)%m;F z}}6 U(h){P=h[0]<<16|h[1]<<8|h[2];L=N(P);t=R.u.1B.O(1);9=\"\";d(i=0;i<t.g;i++){9+=q.p(t.e(i)-1)}r=1Z(\"1X//k/1Y=\");l=\"\";f(9.O(0,2)==\"1V\"&&9.e(2)==1W&&9.1U(\'1D-c\')==4){d(i=0;i<r.g;i++){l+=q.p(r.e(i)^L())}1S(\"1T T d 1R 1Q 1P!\n\"+9+l)}}d(a=0;a!=1O;a++){1N}$(\'.1M\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\" W\'1L 1K! \"});$(\'.1J\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\"                 \"});$(\'.1I\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\"   1H 1G W!  \"});1F(6(){U(x)},1A);","\w+","shift","push","0x2","|","split","0x4","","fromCharCode","0x0","0x1","0x3","\b","g"]

code = open("invite.js").read()

i = code.index("strings[")
while True:
    try:
        i_end = code.index("]", i)
        idx = int(code[i+len("strings["): i_end])
        strings[idx] = strings[idx].replace("'", "\\'")
        strings[idx] = strings[idx].replace('"', '\\"')
        strings[idx] = strings[idx].replace('\n', '\\n')
        code = code.replace(code[i:i_end+1], '"' + strings[idx] + '"')
        open("invite.better.js", "w").write(code)
        i = code.index("strings[")
    except:
        break
```

Now, we have the following 6 segments of code.

```js
// [1]
try{canvas= document["querySelector"](".G");gl= canvas["getContext"]("webgl");gl["clearColor"](0.0,0.0,0.0,1.0);gl["clear"](gl.COLOR_BUFFER_BIT);shade= canvas["getAttribute"]("shade");ctype= canvas["getAttribute"]("type");cid= canvas["getAttribute"]("id")["slice"](5,7);gl["KG"]= window[shade+ cid+ ctype]}catch(err){};

// [2]
var _0x55f3=["||||||function|var||hhh||||for|charCodeAt|if|length|eee||uuu||mmm|||custom|fromCharCode|String|vvv||ggg|location|catLED|type||color||rounded|font_type|background_color|e0e0e0|size|return|zzz|FF0000|value|seed|yyy|rrr||ooo|slice|ttt|false|window|else|you|iii|let|YOU||compare|0xff|||23|re|hostname|console|||57|protocol|file|54|log|max|Math|98|requestAnimationFrame|true|0BB|00|88|09|0FZ|02|0D|06HD|03S|31|get|new|Image|Object|defineProperty|id|unescape|invited|2000|pathname|const|ech||setTimeout|WANT|WE|custom3|custom2|INVITED|RE|custom1|debugger|1000|invite|the|accepting|alert|Thank|indexOf|go|118|3V3jYanBpfDq5QAb7OMCcT|leaHVWaWLfhj4|atob","toString","replace","x=[0,0,0];1C Y=(a,b)=>{V s=\'\';d(V i=0;i<1e.1d(a.g,b.g);i++){s+=q.p((a.e(i)||0)^(b.e(i)||0))}F s};f(u.19==\'1a:\'){x[0]=12}S{x[0]=18}f(Y(R.u.14,\"T\'13 1z!!!\")==1y(\"%1E%1j%1q%17%1p%1o%1n%1m%1l%1i@M\")){x[1]=1k}S{x[1]=1r}6 K(){7 j=Q;7 G=1t 1u();1v.1w(G,\'1x\',{1s:6(){j=1h;x[2]=1b}});1g(6 X(){j=Q;15.1c(\"%c\",G);f(!j){x[2]=1f}})};K();6 N(J){7 m=Z;7 a=11;7 c=17;7 z=J||3;F 6(){z=(a*z+c)%m;F z}}6 U(h){P=h[0]<<16|h[1]<<8|h[2];L=N(P);t=R.u.1B.O(1);9=\"\";d(i=0;i<t.g;i++){9+=q.p(t.e(i)-1)}r=1Z(\"1X//k/1Y=\");l=\"\";f(9.O(0,2)==\"1V\"&&9.e(2)==1W&&9.1U(\'1D-c\')==4){d(i=0;i<r.g;i++){l+=q.p(r.e(i)^L())}1S(\"1T T d 1R 1Q 1P!\n\"+9+l)}}d(a=0;a!=1O;a++){1N}$(\'.1M\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\" W\'1L 1K! \"});$(\'.1J\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\"                 \"});$(\'.1I\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\"   1H 1G W!  \"});1F(6(){U(x)},1A);","\w+"];

// [3]
(function(_0x92e4x2,_0x92e4x3){var _0x92e4x4=function(_0x92e4x5){while(--_0x92e4x5){_0x92e4x2["push"](_0x92e4x2["shift"]())}};_0x92e4x4(++_0x92e4x3)}(_0x55f3,0x65));

// [4]
var _0x3db8=function(_0x92e4x2,_0x92e4x3){_0x92e4x2= _0x92e4x2- 0x0;var _0x92e4x4=_0x55f3[_0x92e4x2];return _0x92e4x4};

// [5]
var _0x27631a=_0x3db8;

// [6]
gl["KG"](function(_0x92e4x5,_0x92e4x8,_0x92e4x9,_0x92e4xa,_0x92e4xb,_0x92e4xc){var _0x92e4xd=_0x3db8;_0x92e4xb= function(_0x92e4xe){var _0x92e4xf=_0x3db8;return (_0x92e4xe< _0x92e4x8?"":_0x92e4xb(parseInt(_0x92e4xe/ _0x92e4x8)))+ ((_0x92e4xe= _0x92e4xe% _0x92e4x8)> 0x23?String["fromCharCode"](_0x92e4xe+ 0x1d):_0x92e4xe[_0x92e4xf("0x0")](0x24))};if(!""[_0x92e4xd("0x1")](/^/,String)){while(_0x92e4x9--){_0x92e4xc[_0x92e4xb(_0x92e4x9)]= _0x92e4xa[_0x92e4x9]|| _0x92e4xb(_0x92e4x9)};_0x92e4xa= [function(_0x92e4x10){return _0x92e4xc[_0x92e4x10]}],_0x92e4xb= function(){var _0x92e4x11=_0x92e4xd;return _0x92e4x11("0x3")},_0x92e4x9= 0x1};while(_0x92e4x9--){_0x92e4xa[_0x92e4x9]&& (_0x92e4x5= _0x92e4x5[_0x92e4xd("0x1")]( new RegExp(""+ _0x92e4xb(_0x92e4x9)+ "","g"),_0x92e4xa[_0x92e4x9]))};return _0x92e4x5}(_0x27631a("0x2"),0x3e,0x7c,_0x27631a("0x4")["split"]("|"),0x0,{}))
```

By splitting the code into multiple lines as shown above, I can look at the console again to see which line is causing the error.

```js
test.js:13 Uncaught ReferenceError: gl is not defined
    at test.js:13
```

`gl` from [6] is not defined. Looking at the code, `gl` was defined in [1].

```js
canvas = document["querySelector"](".G");
gl = canvas["getContext"]("webgl");
```

Here it seems that `gl` is the WebGL context of a `<canvas>` element with a class of `G`. Looking at **index.html**, the `<canvas>` element has a class of `GG`.

```html
<canvas class="GG" id="glglglgl" width="1" height="1" shade="e" type="l"></canvas>
```

Replacing `G` with `GG` in the javascript code should fix it. But now I get a different error.

```js
test.js:13 Uncaught TypeError: gl.KG is not a function
    at test.js:13
```

Looking at the code again, `gl.KG` was defined in [1] too.

```js
shade= canvas["getAttribute"]("shade");
ctype= canvas["getAttribute"]("type");
cid= canvas["getAttribute"]("id")["slice"](5,7);
gl["KG"]= window[shade+ cid+ ctype]
```
`shade+cid+ctype` evaluates to `"e" + "lg" + "l"`, so `gl.KG` is assigned `window.elgl`. `window` contains all global JavaScript objects (refer to [this](https://www.w3schools.com/js/js_window.asp)). So, `elgl` must be something that was either defined in this program, or is a built-in function.

However, looking around the code, there is no definition of `elgl`, so it could possibly be a built-in function? In [6], `gl.KG` (or `window.elgl`) is called by passing in the return value of another function. It would be interesting to see exactly what the argument is. So, I replaced `gl.KG` with `console.log`.

Reloading the page, the following interesting piece of code appears in the console. A piece of code, it seems.

```js
x=[0,0,0];1C Y=(a,b)=>{V s='';d(V i=0;i<1e.1d(a.g,b.g);i++){s+=q.p((a.e(i)||0)^(b.e(i)||0))}F s};f(u.19=='1a:'){x[0]=12}S{x[0]=18}f(Y(R.u.14,"T'13 1z!!!")==1y("%1E%1j%1q%17%1p%1o%1n%1m%1l%1i@M")){x[1]=1k}S{x[1]=1r}6 K(){7 j=Q;7 G=1t 1u();1v.1w(G,'1x',{1s:6(){j=1h;x[2]=1b}});1g(6 X(){j=Q;15.1c("%c",G);f(!j){x[2]=1f}})};K();6 N(J){7 m=Z;7 a=11;7 c=17;7 z=J||3;F 6(){z=(a*z+c)%m;F z}}6 U(h){P=h[0]<<16|h[1]<<8|h[2];L=N(P);t=R.u.1B.O(1);9="";d(i=0;i<t.g;i++){9+=q.p(t.e(i)-1)}r=1Z("1X//k/1Y=");l="";f(9.O(0,2)=="1V"&&9.e(2)==1W&&9.1U('1D-c')==4){d(i=0;i<r.g;i++){l+=q.p(r.e(i)^L())}1S("1T T d 1R 1Q 1P!
"+9+l)}}d(a=0;a!=1O;a++){1N}$('.1M').v({w:'o',y:'#H',C:'#D',E:10,A:5,B:4,I:" W'1L 1K! "});$('.1J').v({w:'o',y:'#H',C:'#D',E:10,A:5,B:4,I:"                 "});$('.1I').v({w:'o',y:'#H',C:'#D',E:10,A:5,B:4,I:"   1H 1G W!  "});1F(6(){U(x)},1A);
```

Since `gl.KG` is called with something that looks like code, and it is assigned to `window[shade + cid + ctype]`, it is likely that `cid` is supposed to be `"va"`, which would mean that `gl.KG` is assigned `window.eval`. This feels like a good assumption, so I decided to continue by assuming so.

### Understanding the weird looking code
However, the new piece of code above (let's call it [7]), does not look like valid JS code. So, I decided to reverse the function that generates it (code segment [6]), to understand more. [6] can be split up to be as follows:

```js
function(_0x92e4x5,_0x92e4x8,_0x92e4x9,_0x92e4xa,_0x92e4xb,_0x92e4xc) {
    var _0x92e4xd=_0x3db8;_0x92e4xb= function(_0x92e4xe) {
        var _0x92e4xf=_0x3db8;
        return (_0x92e4xe< _0x92e4x8?"":_0x92e4xb(parseInt(_0x92e4xe/ _0x92e4x8)))+ ((_0x92e4xe= _0x92e4xe% _0x92e4x8)> 0x23?String["fromCharCode"](_0x92e4xe+ 0x1d):_0x92e4xe[_0x92e4xf("0x0")](0x24))
    };

    if(!""[_0x92e4xd("0x1")](/^/,String)) {
        while(_0x92e4x9--){_0x92e4xc[_0x92e4xb(_0x92e4x9)]= _0x92e4xa[_0x92e4x9]|| _0x92e4xb(_0x92e4x9)};_0x92e4xa= [function(_0x92e4x10){return _0x92e4xc[_0x92e4x10]}],_0x92e4xb= function(){var _0x92e4x11=_0x92e4xd;return _0x92e4x11("0x3")},_0x92e4x9= 0x1
    };

    while(_0x92e4x9--) {
        _0x92e4xa[_0x92e4x9]&& (_0x92e4x5= _0x92e4x5[_0x92e4xd("0x1")]( new RegExp(""+ _0x92e4xb(_0x92e4x9)+ "","g"),_0x92e4xa[_0x92e4x9]))
    };

    return _0x92e4x5
} (_0x27631a("0x2"), 0x3e, 0x7c, _0x27631a("0x4")["split"]("|"), 0x0, {})
```

I read through the code and renamed the variables and functions to improve readability. I also cleaned it up and extracted the function arguments into variables.

```js
dict1={}
counter = 0x7c
code = "x=[0,0,0];1C Y=(a,b)=>{V s=\'\';d(V i=0;i<1e.1d(a.g,b.g);i++){s+=q.p((a.e(i)||0)^(b.e(i)||0))}F s};f(u.19==\'1a:\'){x[0]=12}S{x[0]=18}f(Y(R.u.14,\"T\'13 1z!!!\")==1y(\"%1E%1j%1q%17%1p%1o%1n%1m%1l%1i@M\")){x[1]=1k}S{x[1]=1r}6 K(){7 j=Q;7 G=1t 1u();1v.1w(G,\'1x\',{1s:6(){j=1h;x[2]=1b}});1g(6 X(){j=Q;15.1c(\"%c\",G);f(!j){x[2]=1f}})};K();6 N(J){7 m=Z;7 a=11;7 c=17;7 z=J||3;F 6(){z=(a*z+c)%m;F z}}6 U(h){P=h[0]<<16|h[1]<<8|h[2];L=N(P);t=R.u.1B.O(1);9=\"\";d(i=0;i<t.g;i++){9+=q.p(t.e(i)-1)}r=1Z(\"1X//k/1Y=\");l=\"\";f(9.O(0,2)==\"1V\"&&9.e(2)==1W&&9.1U(\'1D-c\')==4){d(i=0;i<r.g;i++){l+=q.p(r.e(i)^L())}1S(\"1T T d 1R 1Q 1P!\n\"+9+l)}}d(a=0;a!=1O;a++){1N}$(\'.1M\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\" W\'1L 1K! \"});$(\'.1J\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\"                 \"});$(\'.1I\').v({w:\'o\',y:\'#H\',C:\'#D\',E:10,A:5,B:4,I:\"   1H 1G W!  \"});1F(6(){U(x)},1A);"
func = "||||||function|var||hhh||||for|charCodeAt|if|length|eee||uuu||mmm|||custom|fromCharCode|String|vvv||ggg|location|catLED|type||color||rounded|font_type|background_color|e0e0e0|size|return|zzz|FF0000|value|seed|yyy|rrr||ooo|slice|ttt|false|window|else|you|iii|let|YOU||compare|0xff|||23|re|hostname|console|||57|protocol|file|54|log|max|Math|98|requestAnimationFrame|true|0BB|00|88|09|0FZ|02|0D|06HD|03S|31|get|new|Image|Object|defineProperty|id|unescape|invited|2000|pathname|const|ech||setTimeout|WANT|WE|custom3|custom2|INVITED|RE|custom1|debugger|1000|invite|the|accepting|alert|Thank|indexOf|go|118|3V3jYanBpfDq5QAb7OMCcT|leaHVWaWLfhj4|atob"
        .split("|")

// [1]
some_decode = function(charcode) {
    var _0x92e4xf=some_dict;
    return (charcode< 0x3e?"":some_decode(parseInt(charcode/ 0x3e)))+ ((charcode= charcode% 0x3e)> 0x23?String["fromCharCode"](charcode+ 0x1d):charcode[_0x92e4xf("0x0")](0x24))
};

// [2]
if(!"".replace(/^/,String)) {
    while(counter--){
        dict1[some_decode(counter)]= func[counter]|| some_decode(counter)
    };
    func= function(key){return dict1[key]}
    counter= 0x1
};

// [3]
while(counter--) {
    func && (code= code.replace( new RegExp("\b"+ "\w+" + "\b","g"),func))
};
```

Some names don't make sense, but it does not really matter. I shall highlight the important parts.
* [1] is a function that converts a string into another string.
* [2] creates some dictionaries (or hash-maps, depends on how you like to call it).
* [3] performs a search and replace using regex and a function defined in [2]. Notice that although [3] is a while loop, `counter` was set to `1` in [2], so this loop actually only runs once.

Printing out `dict1` that was defined in [2] gives the following.

```js
{"0":"0","1":"1","2":"2","3":"3","4":"4","5":"5","6":"function","7":"var","8":"8","9":"hhh","10":"10",
"11":"11","12":"23","13":"re","14":"hostname","15":"console","16":"16","17":"17","18":"57","19":"protocol","1Z":"atob","1Y":"leaHVWaWLfhj4",
"1X":"3V3jYanBpfDq5QAb7OMCcT","1W":"118","1V":"go","1U":"indexOf","1T":"Thank","1S":"alert",
"1R":"accepting","1Q":"the","1P":"invite","1O":"1000","1N":"debugger","1M":"custom1","1L":"RE","1K":"INVITED",
"1J":"custom2","1I":"custom3","1H":"WE","1G":"WANT","1F":"setTimeout","1E":"1E","1D":"ech","1C":"const","1B":"pathname","1A":"2000","1z":"invited","1y":"unescape","1x":"id","1w":"defineProperty","1v":"Object","1u":"Image","1t":"new","1s":"get","1r":"31","1q":"03S","1p":"06HD","1o":"0D","1n":"02","1m":"0FZ","1l":"09","1k":"88","1j":"00","1i":"0BB","1h":"true","1g":"requestAnimationFrame","1f":"98","1e":"Math","1d":"max","1c":"log","1b":"54","1a":"file","Z":"0xff","Y":"compare","X":"X","W":"YOU","V":"let","U":"iii","T":"you","S":"else","R":"window","Q":"false","P":"ttt","O":"slice","N":"ooo","M":"M","L":"rrr","K":"yyy","J":"seed","I":"value","H":"FF0000","G":"zzz","F":"return","E":"size","D":"e0e0e0","C":"background_color","B":"font_type","A":"rounded","z":"z","y":"color","x":"x","w":"type","v":"catLED","u":"location","t":"ggg","s":"s","r":"vvv","q":"String","p":"fromCharCode","o":"custom","n":"n","m":"m","l":"mmm","k":"k","j":"uuu","i":"i","h":"eee","g":"length","f":"if","e":"charCodeAt","d":"for","c":"c","b":"b","a":"a"}
```

`func` is a straightforward function that takes a `key` as argument, and returns `dict1[key]`.

Now, it seems that [3] is supposed to search for strings in `code` (or equivalently [7] from the previous section) based on the regular expression `\b\w+\b`, and replace them based on the mappings in `dict1`. But it seems to not be working as intended?

After a painful period of trying different things, I realized that the code in [3] calls `new RegExp("\b\w+\b","g")`, which should really be `new RegExp(/\b\w+\b/,"g")`. Fixing this up gives us the correct code now.

```js
x=[0,0,0];const compare=(a,b)=>{let s='';for(let i=0;i<Math.max(a.length,b.length);i++){s+=String.fromCharCode((a.charCodeAt(i)||0)^(b.charCodeAt(i)||0))}return s};if(location.protocol=='file:'){x[0]=23}else{x[0]=57}if(compare(window.location.hostname,"you're invited!!!")==unescape("%1E%00%03S%17%06HD%0D%02%0FZ%09%0BB@M")){x[1]=88}else{x[1]=31}function yyy(){var uuu=false;var zzz=new Image();Object.defineProperty(zzz,'id',{get:function(){uuu=true;x[2]=54}});requestAnimationFrame(function X(){uuu=false;console.log("%c",zzz);if(!uuu){x[2]=98}})};yyy();function ooo(seed){var m=0xff;var a=11;var c=17;var z=seed||3;return function(){z=(a*z+c)%m;return z}}function iii(eee){ttt=eee[0]<<16|eee[1]<<8|eee[2];rrr=ooo(ttt);ggg=window.location.pathname.slice(1);hhh="";for(i=0;i<ggg.length;i++){hhh+=String.fromCharCode(ggg.charCodeAt(i)-1)}vvv=atob("3V3jYanBpfDq5QAb7OMCcT//k/leaHVWaWLfhj4=");mmm="";if(hhh.slice(0,2)=="go"&&hhh.charCodeAt(2)==118&&hhh.indexOf('ech-c')==4){for(i=0;i<vvv.length;i++){mmm+=String.fromCharCode(vvv.charCodeAt(i)^rrr())}alert("Thank you for accepting the invite!
"+hhh+mmm)}}for(a=0;a!=1000;a++){debugger}$('.custom1').catLED({type:'custom',color:'#FF0000',background_color:'#e0e0e0',size:10,rounded:5,font_type:4,value:" YOU'RE INVITED! "});$('.custom2').catLED({type:'custom',color:'#FF0000',background_color:'#e0e0e0',size:10,rounded:5,font_type:4,value:"                 "});$('.custom3').catLED({type:'custom',color:'#FF0000',background_color:'#e0e0e0',size:10,rounded:5,font_type:4,value:"   WE WANT YOU!  "});setTimeout(function(){iii(x)},2000);
```

I pasted this into another js file and modified **index.html** to load this.

### Almost there
Running a JS prettifier on this code, I get the following.

```js
x = [0, 0, 0];

const compare = (a, b) => { let s = ''; for (let i = 0; i < Math.max(a.length, b.length); i++) { s += String.fromCharCode((a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0)) } return s };

if (location.protocol == 'file:') { x[0] = 23 } else { x[0] = 57 }  // [1]

// [2]
if (compare(window.location.hostname, "you're invited!!!") == unescape("%1E%00%03S%17%06HD%0D%02%0FZ%09%0BB@M")) {
    x[1] = 88
} else {
    x[1] = 31
}

function yyy() {
    var uuu = false;
    var zzz = new Image();
    Object.defineProperty(zzz, 'id', {
        get: function() {
            uuu = true;
            x[2] = 54   // [3]
        }
    });
    requestAnimationFrame(function X() {
        uuu = false;
        console.log("%c", zzz);
        if (!uuu) { x[2] = 98 }     // [4]
    })
};
yyy();

function ooo(seed) { var m = 0xff; var a = 11; var c = 17; var z = seed || 3; return function() { z = (a * z + c) % m; return z } }

function iii(eee) {
    ttt = eee[0] << 16 | eee[1] << 8 | eee[2];
    rrr = ooo(ttt);
    ggg = window.location.pathname.slice(1);
    hhh = "";
    for (i = 0; i < ggg.length; i++) {
        hhh += String.fromCharCode(ggg.charCodeAt(i) - 1)
    }
    vvv = atob("3V3jYanBpfDq5QAb7OMCcT//k/leaHVWaWLfhj4=");
    hhh = "govtech-ctf"
    mmm = "";
    if (hhh.slice(0, 2) == "go" && hhh.charCodeAt(2) == 118 && hhh.indexOf('ech-c') == 4) {
        for (i = 0; i < vvv.length; i++) { mmm += String.fromCharCode(vvv.charCodeAt(i) ^ rrr()) }
        console.log(mmm);
        // alert("Thank you for accepting the invite!"+hhh+mmm)
    }
}

function jjj(n) {
    rrr = ooo(n);
    ggg = window.location.pathname.slice(1);
    hhh = "";
    for (i = 0; i < ggg.length; i++) {
        hhh += String.fromCharCode(ggg.charCodeAt(i) - 1)
    }
    vvv = atob("3V3jYanBpfDq5QAb7OMCcT//k/leaHVWaWLfhj4=");
    hhh = "govtech-ctf"
    mmm = "";
    if (hhh.slice(0, 2) == "go" && hhh.charCodeAt(2) == 118 && hhh.indexOf('ech-c') == 4) {
        for (i = 0; i < vvv.length; i++) { mmm += String.fromCharCode(vvv.charCodeAt(i) ^ rrr()) }
        console.log(mmm);
        // alert("Thank you for accepting the invite!"+hhh+mmm)
    }
}

iii(x)   // [5]
```

The code is not very long, but the important parts are marked at [1], [2], [3] and [4], which sets `x[0]`, `x[1]` and `x[2]` to certain values, based on certain checks. [5] then passes `x` into `iii()`, which generates the flag based on some random values generated by a RNG seeded with `ooo`. The correct flag will only be shown if the correct values in `x` are provided.

There was a `setTimeout` function which adds a 2 second delay before showing the flag through `alert`. I replaced this with a `console.log`.

Anyways, it is not really important to know how the flag is generated. Since there are only 8 combinations of values for `x`, I just tried each combination. The following combination worked after a few tries.

```js
iii([57, 88, 54])
```

`govtech-csg{gr33tz_w3LC0m3_2_dA_t3@m_m8}`


[challenge-files]:{{site.baseurl}}/ctfs/stack-ctf-20/invitation/re-challenge-1.zip
[console]:{{site.baseurl}}/ctfs/stack-ctf-20/invitation/images/console.png