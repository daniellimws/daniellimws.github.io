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
        System.out.println("Hi");
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
                // fos.close(); There is no more need for this line since you had created the
                // instance of "fos" inside the try. And this will automatically close the
                // OutputStream
            }
        } catch (IOException ex) {
            // ignore close exception
        }
    }
}
