import java.io.*;
import java.net.*;
import java.nio.file.*;
public class SandboxProbe {
  interface Attempt {void run() throws Exception;}
  static void denied(String name,Attempt attempt) throws Exception {
    try {attempt.run();throw new RuntimeException("Guard did not reject "+name);}
    catch(SecurityException expected){System.out.println(name+":DENIED");}
  }
  public static void main(String[] args) throws Exception {
    if(System.getSecurityManager()==null)throw new RuntimeException("No active sandbox");
    denied("network",()->new Socket("127.0.0.1",9).close());
    denied("external_file",()->Files.readString(Path.of(args[0])));
    denied("process_execution",()->new ProcessBuilder("not-a-real-synthetic-executable").start());
    denied("file_write",()->Files.writeString(Path.of("write-probe.txt"),"synthetic"));
  }
}
