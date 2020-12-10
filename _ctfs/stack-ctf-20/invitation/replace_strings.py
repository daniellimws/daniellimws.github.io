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