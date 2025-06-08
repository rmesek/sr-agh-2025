import org.apache.zookeeper.*;
import org.apache.zookeeper.data.Stat;

import javax.swing.JOptionPane;
import java.io.IOException;
import java.util.List;
import java.util.Scanner;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Semaphore;

public class ZooKeeperWatcher implements Watcher {
    private ZooKeeper zooKeeper;
    private final String externalAppPath;
    private Process externalProcess;
    private final String NODE_PATH = "/a";
    private final Semaphore connectedSemaphore = new Semaphore(0);

    public ZooKeeperWatcher(String hosts, String appPath) {
        this.externalAppPath = appPath;
        try {
            zooKeeper = new ZooKeeper(hosts, 3000, this);
            connectedSemaphore.acquire();

            Stat stat = zooKeeper.exists(NODE_PATH, true);
            if (stat != null) {
                startExternalApp();
                watchChildren();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Override
    public void process(WatchedEvent event) {
        if (event.getState() == Event.KeeperState.SyncConnected) {
            connectedSemaphore.release();
        }

        if (event.getPath() != null && event.getPath().equals(NODE_PATH)) {
            if (event.getType() == Event.EventType.NodeCreated) {
                startExternalApp();
                watchChildren();
            } else if (event.getType() == Event.EventType.NodeDeleted) {
                stopExternalApp();
            } else if (event.getType() == Event.EventType.NodeChildrenChanged) {
                watchChildren();
            }
            try {
                zooKeeper.exists(NODE_PATH, true);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private void watchChildren() {
        try {
            List<String> children = zooKeeper.getChildren(NODE_PATH, true);
            showChildrenCount(children.size());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void startExternalApp() {
        try {
            ProcessBuilder pb = new ProcessBuilder(externalAppPath);
            externalProcess = pb.start();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void stopExternalApp() {
        if (externalProcess != null) {
            externalProcess.destroyForcibly();
            externalProcess = null;
        }
    }

    private void showChildrenCount(int count) {
        String message = "Node /a has " + count + " children";
        JOptionPane.showMessageDialog(null, message);
    }

    public void printTree() {
        try {
            Stat stat = zooKeeper.exists(NODE_PATH, false);
            if (stat != null) {
                String treeStructure = buildNodeString(NODE_PATH, "");
                JOptionPane.showMessageDialog(null, "Tree \n" + treeStructure);
            } else {
                JOptionPane.showMessageDialog(null, "Tree \n");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private String buildNodeString(String path, String indent) {
        StringBuilder result = new StringBuilder();
        try {
            result.append(indent).append(path).append("\n");
            List<String> children = zooKeeper.getChildren(path, false);
            for (String child : children) {
                String childPath = path + "/" + child;
                result.append(buildNodeString(childPath, indent + "."));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return result.toString();
    }

    public void close() {
        try {
            stopExternalApp();
            if (zooKeeper != null) zooKeeper.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: java ZooKeeperWatcher localhost:2181 notepad.exe");
            return;
        }

        String zooKeeperHosts = args[0];
        String externalAppPath = args[1];

        ZooKeeperWatcher watcher = new ZooKeeperWatcher(zooKeeperHosts, externalAppPath);

        Runtime.getRuntime().addShutdownHook(new Thread(watcher::close));

        Scanner scanner = new Scanner(System.in);
        System.out.println("Press 't' to display tree structure, 'q' to quit");

        while (true) {
            String input = scanner.nextLine().trim().toLowerCase();
            if ("t".equals(input)) watcher.printTree();
            else if ("q".equals(input)) System.exit(0);
        }
    }
}