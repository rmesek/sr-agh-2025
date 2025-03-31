import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.nio.ByteOrder;

public class JavaUdpServer {

    public static void main(String args[]) {
        System.out.println("JAVA UDP SERVER");
        DatagramSocket socket = null;
        int portNumber = 9008;

        try {
            socket = new DatagramSocket(portNumber);
            byte[] receiveBuffer = new byte[1024];
            byte[] sendBuffer = new byte[1024];

            while (true) {
                Arrays.fill(receiveBuffer, (byte) 0);
                DatagramPacket receivePacket = new DatagramPacket(receiveBuffer, receiveBuffer.length);
                socket.receive(receivePacket);
                int nb = ByteBuffer.wrap(receivePacket.getData()).order(ByteOrder.LITTLE_ENDIAN).getInt();
                System.out.println("received msg: " + nb);

                InetAddress clientAddress = receivePacket.getAddress();
                int clientPortNumber = receivePacket.getPort();
                nb = nb + 1;
                sendBuffer = ByteBuffer.allocate(4).putInt(nb).array();
                DatagramPacket sendPacket = new DatagramPacket(sendBuffer, sendBuffer.length, clientAddress,
                        clientPortNumber);
                socket.send(sendPacket);
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (socket != null) {
                socket.close();
            }
        }
    }
}
